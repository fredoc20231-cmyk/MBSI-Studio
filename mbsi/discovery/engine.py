"""Biopharma Discovery Engine orchestrator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad

from mbsi.discovery.findings_builder import build_dos_findings
from mbsi.notebook.notebook import append_run
from mbsi.registry.registry import ProjectRegistry
from mbsi.reports.biomarker_report import (
    generate_biomarker_report_text,
    BIOMARKER_DISCLAIMER,
)
from mbsi.validation.recommendations import recommend_validations


def run_discovery_engine(
    adata: Optional[ad.AnnData] = None,
    seed: int = 42,
    benchmark_methods: Optional[list] = None,
    readiness: Optional[Dict[str, Any]] = None,
    dataset_id: str = "default",
) -> Dict[str, Any]:
    """Run full Biopharma Discovery Engine v1 pipeline with graceful degradation."""
    from mbsi.tme import make_tme_demo_adata

    warnings: List[str] = []
    if adata is None:
        adata = make_tme_demo_adata(n_spots=100, seed=seed)

    if readiness is None and adata is not None:
        readiness = adata.uns.get("mbsi_readiness")

    benchmark: Dict[str, Any] = {}
    communication: Dict[str, Any] = {}
    tme: Dict[str, Any] = {}

    try:
        from mbsi.benchmarks.hub import run_benchmark_hub
        benchmark = run_benchmark_hub(
            ground_truth_adata=adata if adata.n_obs >= 50 else None,
            methods=benchmark_methods or ["mbsi", "tangram"],
            seed=seed,
            dataset_mode="session" if adata is not None else "synthetic",
            session_adata=adata,
            synthetic_cells=max(80, adata.n_obs),
            n_spots=min(80, adata.n_obs),
        )
    except Exception as exc:
        warnings.append(f"Benchmark Hub failed: {exc}")

    try:
        from mbsi.communication import run_communication_analysis, make_communication_demo_adata
        comm_adata = adata if "CXCL12" in adata.var_names else make_communication_demo_adata(n_spots=adata.n_obs, seed=seed)
        communication = run_communication_analysis(comm_adata, k=6)
    except Exception as exc:
        warnings.append(f"Communication analysis failed: {exc}")

    try:
        from mbsi.tme import run_tme_analysis
        tme = run_tme_analysis(adata)
    except Exception as exc:
        warnings.append(f"TME analysis failed: {exc}")

    store, graph = build_dos_findings(benchmark, communication, tme, readiness)
    findings = store.list_findings()
    evidence = store.list_evidence()
    validations = recommend_validations(findings)

    notebook_entry = append_run(
        findings=findings,
        evidence=evidence,
        summary=f"Discovery run seed={seed}, {len(findings)} findings",
    )

    registry = ProjectRegistry()
    run_record = registry.register_run(
        dataset_id=dataset_id,
        finding_ids=[f.finding_id for f in findings],
        metadata={"seed": seed, "status": "complete" if not warnings else "complete_with_warnings"},
    )

    actionable = _build_actionable_findings(benchmark, communication, tme)
    actionable.extend([
        {
            "type": f.finding_type,
            "title": f.title,
            "detail": f.summary,
            "priority": "high" if f.confidence_level == "High" else "medium",
            "confidence_score": f.confidence_score,
            "confidence_level": f.confidence_level,
        }
        for f in findings[:5]
    ])

    status = "complete" if not warnings else "complete_with_warnings"

    return {
        "adata": adata,
        "benchmark_results": benchmark,
        "communication_results": communication,
        "tme_results": tme,
        "findings": [f.to_dict() for f in findings],
        "evidence": [e.to_dict() for e in evidence],
        "discovery_graph": graph,
        "validation_recommendations": validations,
        "notebook_entry": notebook_entry.to_dict(),
        "run_id": run_record["run_id"],
        "actionable_findings": actionable,
        "warnings": warnings,
        "status": status,
        "disclaimer": BIOMARKER_DISCLAIMER,
        "report_text": generate_biomarker_report_text(benchmark or None, communication or None, tme or None),
    }


def _build_actionable_findings(benchmark, communication, tme) -> list:
    findings = []
    lb = benchmark.get("leaderboard") if isinstance(benchmark, dict) else None
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        top = lb.iloc[0]
        findings.append({
            "type": "benchmark",
            "title": f"Best reconstruction: {top['method']}",
            "detail": f"Gene Pearson {top.get('gene_pearson', 0):.3f} (computational hypothesis)",
            "priority": "high",
        })
    if isinstance(communication, dict) and communication.get("top_pathway"):
        findings.append({
            "type": "communication",
            "title": f"Top signaling: {communication['top_pathway']}",
            "detail": "L-R pathway enrichment detected spatially",
            "priority": "medium",
        })
    summary = tme.get("summary") if isinstance(tme, dict) else None
    if summary is not None and hasattr(summary, "empty") and not summary.empty:
        top_niche = summary.iloc[0]
        findings.append({
            "type": "tme",
            "title": f"Dominant niche: {top_niche['niche_type']}",
            "detail": f"{int(top_niche['n_spots_detected'])} spots flagged",
            "priority": "medium",
        })
    return findings


def export_discovery_engine(results: Dict[str, Any], out_dir) -> None:
    """Export all discovery engine outputs (skip missing modules)."""
    from pathlib import Path
    import json
    import shutil

    from mbsi.graph.export import export_graph_json
    from mbsi.reports.biomarker_report import generate_spatial_biomarker_report

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bench = results.get("benchmark_results") or {}
    comm = results.get("communication_results") or {}
    tme = results.get("tme_results") or {}

    try:
        if bench:
            from mbsi.benchmarks.export import export_benchmark_hub
            export_benchmark_hub(bench, out_dir)
    except Exception:
        pass
    try:
        if comm:
            from mbsi.communication import export_communication_results
            export_communication_results(comm, out_dir)
    except Exception:
        pass
    try:
        if tme:
            from mbsi.tme import export_tme_results
            export_tme_results(tme, out_dir)
    except Exception:
        pass

    if bench or comm or tme:
        report_path = generate_spatial_biomarker_report(bench or None, comm or None, tme or None, out_dir)
        shutil.copy(report_path, out_dir / "biopharma_discovery_report.html")

    if results.get("discovery_graph"):
        export_graph_json(results["discovery_graph"], out_dir / "discovery_graph.json")

    if results.get("findings"):
        (out_dir / "findings.json").write_text(
            json.dumps({"findings": results["findings"], "evidence": results.get("evidence", [])}, indent=2, default=str)
        )

    (out_dir / "discovery_engine_summary.json").write_text(
        json.dumps({
            "disclaimer": results.get("disclaimer"),
            "status": results.get("status"),
            "warnings": results.get("warnings", []),
            "actionable_findings": results.get("actionable_findings", []),
            "n_findings": len(results.get("findings", [])),
            "run_id": results.get("run_id"),
        }, indent=2, default=str)
    )
