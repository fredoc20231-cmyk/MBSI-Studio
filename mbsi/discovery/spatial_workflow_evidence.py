"""Evidence builders for spatialGE workflow modules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from mbsi.confidence.engine import score_finding
from mbsi.discovery.findings_builder import _attach_sample_context
from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.evidence import create_evidence
from mbsi.discovery_model.finding_store import FindingStore
from mbsi.discovery_model.ontology import FindingType


def _store() -> FindingStore:
    return FindingStore()


def svg_to_evidence(
    svg_table: pd.DataFrame,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
    top_n: int = 10,
) -> Tuple[FindingStore, List[str]]:
    """Convert spatial variable gene table to Finding + Evidence."""
    store = _store()
    warnings: List[str] = []
    if svg_table.empty:
        warnings.append("No SVG results to convert.")
        return store, warnings

    top = svg_table.head(top_n)
    genes = top["gene"].tolist() if "gene" in top.columns else []
    evidence_list = []
    for _, row in top.iterrows():
        gene = row.get("gene", "")
        ev = create_evidence(
            "spatial_variable_genes",
            "spatial_svg",
            str(gene),
            description=f"Moran I={row.get('morans_i', '—')}, Geary C={row.get('gearys_c', '—')}",
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title="Spatially variable genes detected",
        summary=f"Top SVG: {', '.join(genes[:5])}",
        finding_type=FindingType.BIOMARKER.value,
        module="spatial_variable_genes",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, warnings


def enrichment_to_evidence(
    enrich_table: pd.DataFrame,
    library: str,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
) -> Tuple[FindingStore, List[str]]:
    store = _store()
    warnings: List[str] = []
    if enrich_table.empty:
        warnings.append("No enrichment results.")
        return store, warnings

    term_col = "Term" if "Term" in enrich_table.columns else enrich_table.columns[0]
    top_term = str(enrich_table.iloc[0].get(term_col, "pathway"))
    evidence_list = []
    for _, row in enrich_table.head(5).iterrows():
        ev = create_evidence(
            "spatial_gene_sets",
            "enrichment",
            str(row.get(term_col, "term")),
            description=library,
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title=f"Gene set enrichment ({library})",
        summary=f"Top term: {top_term}",
        finding_type=FindingType.PATHWAY.value,
        module="spatial_gene_sets",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, warnings


def domain_to_finding(
    domain_summary: pd.DataFrame,
    method: str,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
) -> Tuple[FindingStore, List[str]]:
    store = _store()
    evidence_list = []
    for _, row in domain_summary.iterrows():
        ev = create_evidence(
            "spatial_domains",
            "spatial_domain",
            f"Domain {row.get('domain', '')}",
            description=f"{row.get('n_spots', 0)} spots",
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title=f"Spatial domains ({method})",
        summary=f"{len(domain_summary)} domains identified",
        finding_type=FindingType.NICHE.value,
        module="spatial_domains",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, []


def phenotype_to_evidence(
    phenotype_table: pd.DataFrame,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
) -> Tuple[FindingStore, List[str]]:
    store = _store()
    if phenotype_table.empty:
        return store, ["No phenotype scores."]
    evidence_list = []
    for _, row in phenotype_table.iterrows():
        ev = create_evidence(
            "phenotyping",
            "phenotype",
            str(row.get("panel", row.get("compartment", "score"))),
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title="Cell phenotyping scores",
        summary=f"{len(phenotype_table)} compartment scores computed",
        finding_type=FindingType.NICHE.value,
        module="phenotyping",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, []


def de_to_evidence(
    de_table: pd.DataFrame,
    mode: str,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
    top_n: int = 10,
) -> Tuple[FindingStore, List[str]]:
    store = _store()
    if de_table.empty:
        return store, [f"No DE results for mode={mode}."]
    top = de_table.head(top_n)
    genes = top["gene"].tolist() if "gene" in top.columns else []
    evidence_list = []
    for _, row in top.iterrows():
        ev = create_evidence(
            "differential_analysis",
            "differential_expression",
            str(row.get("gene", "")),
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title=f"Differential expression ({mode})",
        summary=f"Top DE genes: {', '.join(genes[:5])}",
        finding_type=FindingType.BIOMARKER.value,
        module="differential_analysis",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, []


def gradient_to_evidence(
    gradient_table: pd.DataFrame,
    mode: str,
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
) -> Tuple[FindingStore, List[str]]:
    store = _store()
    if gradient_table.empty:
        return store, ["No gradient results."]
    evidence_list = []
    for _, row in gradient_table.head(5).iterrows():
        ev = create_evidence(
            "spatial_gradients",
            "spatial_gradient",
            str(row.get("gene", "")),
            description=mode,
            value=row.to_dict(),
        )
        store.add_evidence(ev)
        evidence_list.append(ev)

    finding = Finding.create(
        title=f"Spatial gradient ({mode})",
        summary=f"Gradient analysis across {len(gradient_table)} genes",
        finding_type=FindingType.NICHE.value,
        module="spatial_gradients",
        evidence_ids=[e.evidence_id for e in evidence_list],
    )
    score_finding(finding, evidence_list, readiness=readiness)
    store.add(_attach_sample_context(finding, readiness, run_id=run_id))
    return store, []
