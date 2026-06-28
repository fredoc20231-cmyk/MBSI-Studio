"""Biopharma Discovery Engine orchestrator."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad

from mbsi.benchmarks.hub import run_benchmark_hub
from mbsi.communication import run_communication_analysis, make_communication_demo_adata
from mbsi.tme import run_tme_analysis, make_tme_demo_adata
from mbsi.reports.biomarker_report import (
    generate_spatial_biomarker_report,
    generate_biomarker_report_text,
    BIOMARKER_DISCLAIMER,
)


def run_discovery_engine(
    adata: Optional[ad.AnnData] = None,
    seed: int = 42,
    benchmark_methods: Optional[list] = None,
) -> Dict[str, Any]:
    """Run full Biopharma Discovery Engine v1 pipeline."""
    if adata is None:
        adata = make_tme_demo_adata(n_spots=100, seed=seed)

    benchmark = run_benchmark_hub(
        ground_truth_adata=adata if adata.n_obs >= 50 else None,
        methods=benchmark_methods or ["mbsi", "tangram"],
        seed=seed,
        dataset_mode="session" if adata is not None else "synthetic",
        session_adata=adata,
        synthetic_cells=max(80, adata.n_obs),
        n_spots=min(80, adata.n_obs),
    )

    comm_adata = adata if "CXCL12" in adata.var_names else make_communication_demo_adata(n_spots=adata.n_obs, seed=seed)
    communication = run_communication_analysis(comm_adata, k=6)
    tme = run_tme_analysis(adata)

    actionable = _build_actionable_findings(benchmark, communication, tme)

    return {
        "adata": adata,
        "benchmark_results": benchmark,
        "communication_results": communication,
        "tme_results": tme,
        "actionable_findings": actionable,
        "disclaimer": BIOMARKER_DISCLAIMER,
        "report_text": generate_biomarker_report_text(benchmark, communication, tme),
    }


def _build_actionable_findings(benchmark, communication, tme) -> list:
    findings = []
    lb = benchmark.get("leaderboard")
    if lb is not None and not lb.empty:
        top = lb.iloc[0]
        findings.append({
            "type": "benchmark",
            "title": f"Best reconstruction: {top['method']}",
            "detail": f"Gene Pearson {top.get('gene_pearson', 0):.3f} (computational hypothesis)",
            "priority": "high",
        })
    if communication.get("top_pathway"):
        findings.append({
            "type": "communication",
            "title": f"Top signaling: {communication['top_pathway']}",
            "detail": "L-R pathway enrichment detected spatially",
            "priority": "medium",
        })
    summary = tme.get("summary")
    if summary is not None and not summary.empty:
        top_niche = summary.iloc[0]
        findings.append({
            "type": "tme",
            "title": f"Dominant niche: {top_niche['niche_type']}",
            "detail": f"{int(top_niche['n_spots_detected'])} spots flagged",
            "priority": "medium",
        })
    return findings


def export_discovery_engine(results: Dict[str, Any], out_dir) -> None:
    """Export all discovery engine outputs."""
    from pathlib import Path
    import json
    import shutil

    from mbsi.benchmarks.export import export_benchmark_hub
    from mbsi.communication import export_communication_results
    from mbsi.tme import export_tme_results

    out_dir = Path(out_dir)
    export_benchmark_hub(results["benchmark_results"], out_dir)
    export_communication_results(results["communication_results"], out_dir)
    export_tme_results(results["tme_results"], out_dir)
    report_path = generate_spatial_biomarker_report(
        results["benchmark_results"],
        results["communication_results"],
        results["tme_results"],
        out_dir,
    )
    shutil.copy(report_path, out_dir / "biopharma_discovery_report.html")
    (out_dir / "discovery_engine_summary.json").write_text(
        json.dumps({
            "disclaimer": results["disclaimer"],
            "actionable_findings": results["actionable_findings"],
        }, indent=2, default=str)
    )
