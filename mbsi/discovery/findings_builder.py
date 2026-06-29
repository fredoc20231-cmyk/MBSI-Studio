"""Convert pipeline outputs into DOS Finding + Evidence objects."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from mbsi.confidence.engine import score_finding
from mbsi.schema.finding import finding_with_sample_context
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.sample import SampleRecord
from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.evidence import create_evidence
from mbsi.discovery_model.finding_store import FindingStore
from mbsi.discovery_model.ontology import FindingType
from mbsi.graph.builder import build_discovery_graph


def _sample_context(readiness: Optional[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """Extract primary sample context from project setup readiness payload."""
    if not readiness:
        return {}
    samples = readiness.get("sample_metadata")
    if not samples:
        return {}
    row: Dict[str, Any]
    if isinstance(samples, list) and samples:
        row = samples[0] if isinstance(samples[0], dict) else {}
    elif hasattr(samples, "iloc"):
        row = samples.iloc[0].to_dict()
    else:
        return {}

    design = readiness.get("experimental_design") or {}
    comparison = design.get("comparison_groups") or row.get("condition")
    return {
        "sample_id": row.get("sample_id"),
        "condition": row.get("condition"),
        "replicate_id": row.get("replicate_id"),
        "platform": row.get("platform") or (readiness.get("platform_metadata") or {}).get("platforms", [None])[0]
        if (readiness.get("platform_metadata") or {}).get("platforms")
        else None,
        "comparison_group": comparison,
    }


def _attach_sample_context(finding: Finding, readiness: Optional[Dict[str, Any]]) -> Finding:
    ctx = _sample_context(readiness)
    if not ctx or not ctx.get("sample_id"):
        for field in ("sample_id", "condition", "replicate_id", "platform", "comparison_group"):
            val = ctx.get(field)
            if val is not None:
                setattr(finding, field, val)
        return finding
    sample = SampleRecord.from_dict(
        {
            "sample_id": str(ctx.get("sample_id", "")),
            "condition": str(ctx.get("condition", "")),
            "replicate_id": str(ctx.get("replicate_id", "")),
            "platform": str(ctx.get("platform", "")),
            "comparison_group": str(ctx.get("comparison_group", "")),
        }
    )
    return finding_with_sample_context(finding, sample=sample, comparison_group=ctx.get("comparison_group"))


def _niche_finding_type(niche_type: str) -> str:
    niche_lower = (niche_type or "").lower()
    if "immune" in niche_lower or "exclusion" in niche_lower:
        return FindingType.IMMUNE_EXCLUSION.value
    if "hypox" in niche_lower:
        return FindingType.HYPOXIA_NICHE.value
    if "caf" in niche_lower or "stroma" in niche_lower:
        return FindingType.CAF_BARRIER.value
    return FindingType.NICHE.value


def build_dos_findings(
    benchmark: Dict[str, Any],
    communication: Dict[str, Any],
    tme: Dict[str, Any],
    readiness: Optional[Dict[str, Any]] = None,
) -> Tuple[FindingStore, Dict[str, Any]]:
    """Convert benchmark/communication/tme outputs to scored Finding objects."""
    store = FindingStore()

    if isinstance(benchmark, dict):
        lb = benchmark.get("leaderboard")
        if lb is not None and hasattr(lb, "empty") and not lb.empty:
            top = lb.iloc[0]
            ev = create_evidence(
                "benchmark", "metric", "Leaderboard top method",
                description=f"Gene Pearson {top.get('gene_pearson', 0):.3f}",
                value=float(top.get("gene_pearson", 0)),
            )
            store.add_evidence(ev)
            finding = Finding.create(
                title=f"Best reconstruction: {top['method']}",
                summary=f"Top benchmark method {top['method']} with gene Pearson {top.get('gene_pearson', 0):.3f}",
                finding_type=FindingType.BENCHMARK.value,
                module="benchmark",
                evidence_ids=[ev.evidence_id],
                metadata={"method": top["method"], "gene_pearson": float(top.get("gene_pearson", 0))},
            )
            score_finding(finding, [ev], benchmark, readiness)
            store.add(_attach_sample_context(finding, readiness))

    if isinstance(communication, dict):
        top_pathway = communication.get("top_pathway")
        if top_pathway:
            ev = create_evidence(
                "communication", "pathway", f"Pathway: {top_pathway}",
                description="Top L-R pathway from spatial communication analysis",
                value=top_pathway,
            )
            store.add_evidence(ev)
            finding = Finding.create(
                title=f"Top signaling: {top_pathway}",
                summary=f"L-R pathway {top_pathway} enriched in spatial communication analysis",
                finding_type=FindingType.LR_PATHWAY.value,
                module="communication",
                evidence_ids=[ev.evidence_id],
            )
            score_finding(finding, [ev], benchmark, readiness)
            store.add(_attach_sample_context(finding, readiness))

        rankings = communication.get("pathway_rankings")
        if rankings is not None and hasattr(rankings, "head"):
            for _, row in rankings.head(3).iterrows():
                pname = row.get("pathway_name") or row.get("pathway", "pathway")
                ev = create_evidence(
                    "communication", "pathway", str(pname),
                    value=float(row.get("score", row.get("pathway_score", 0))),
                )
                store.add_evidence(ev)
                finding = Finding.create(
                    title=f"Pathway enrichment: {pname}",
                    summary=f"Communication pathway {pname} ranked in top pathways",
                    finding_type=FindingType.PATHWAY.value,
                    module="communication",
                    evidence_ids=[ev.evidence_id],
                )
                score_finding(finding, [ev], benchmark, readiness)
                store.add(_attach_sample_context(finding, readiness))

    if isinstance(tme, dict):
        summary = tme.get("summary")
        if summary is not None and hasattr(summary, "empty") and not summary.empty:
            for _, row in summary.head(3).iterrows():
                niche = row.get("niche_type", "niche")
                n_spots = int(row.get("n_spots_detected", 0))
                ev = create_evidence(
                    "tme", "niche", f"Niche: {niche}",
                    description=f"{n_spots} spots detected",
                    value=n_spots,
                )
                store.add_evidence(ev)
                ftype = _niche_finding_type(str(niche))
                finding = Finding.create(
                    title=f"Dominant niche: {niche}",
                    summary=f"TME niche {niche} detected in {n_spots} spots",
                    finding_type=ftype,
                    module="tme",
                    evidence_ids=[ev.evidence_id],
                    metadata={"n_spots": n_spots},
                )
                score_finding(finding, [ev], benchmark, readiness)
                store.add(_attach_sample_context(finding, readiness))

        prog = tme.get("program_summary")
        if prog is not None and hasattr(prog, "head"):
            for _, row in prog.head(2).iterrows():
                program = row.get("program", row.get("program_name", "program"))
                score_val = float(row.get("mean_score", row.get("score", 0)))
                ev = create_evidence(
                    "tme", "metric", f"TME program: {program}",
                    value=score_val,
                )
                store.add_evidence(ev)
                finding = Finding.create(
                    title=f"TME program: {program}",
                    summary=f"Marker program {program} elevated (score {score_val:.2f})",
                    finding_type=FindingType.TME_PROGRAM.value,
                    module="tme",
                    evidence_ids=[ev.evidence_id],
                )
                score_finding(finding, [ev], benchmark, readiness)
                store.add(_attach_sample_context(finding, readiness))

        biomarkers = tme.get("biomarkers")
        if biomarkers is None:
            biomarkers = tme.get("biomarker_candidates")
        if biomarkers is not None and hasattr(biomarkers, "head"):
            for _, row in biomarkers.head(3).iterrows():
                gene = row.get("gene", row.get("marker", "marker"))
                ev = create_evidence(
                    "tme", "metric", f"Biomarker candidate: {gene}",
                    value=gene,
                )
                store.add_evidence(ev)
                finding = Finding.create(
                    title=f"Biomarker candidate: {gene}",
                    summary=f"Spatial biomarker candidate {gene} flagged by TME analysis",
                    finding_type=FindingType.BIOMARKER.value,
                    module="tme",
                    evidence_ids=[ev.evidence_id],
                )
                score_finding(finding, [ev], benchmark, readiness)
                store.add(_attach_sample_context(finding, readiness))

    graph = build_discovery_graph(store.list_findings(), store.list_evidence())
    return store, graph
