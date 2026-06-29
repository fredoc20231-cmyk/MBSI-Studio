"""Validation recommendations per finding type."""

from __future__ import annotations

from typing import Any, Dict, List

from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.ontology import FindingType


_RECOMMENDATIONS: Dict[str, List[str]] = {
    FindingType.IMMUNE_EXCLUSION: [
        "Multiplex IF for CD8+ T cells vs tumor/stroma boundary",
        "Spatial deconvolution validation with orthogonal scRNA-seq",
        "Perturbation: checkpoint blockade ex vivo slice culture",
    ],
    FindingType.CAF_BARRIER: [
        "IF/IHC for α-SMA, FAP, collagen deposition",
        "Spatial proximity analysis CAF–immune interfaces",
        "CAF-targeted perturbation (FAP inhibitor) in organoid co-culture",
    ],
    FindingType.LR_PATHWAY: [
        "RT-qPCR for top ligand/receptor pairs",
        "Spatial IF co-localization of L-R partners",
        "Pathway inhibitor perturbation (e.g. receptor blockade)",
    ],
    FindingType.HYPOXIA_NICHE: [
        "Hypoxia probe (pimonidazole) IF",
        "HIF1A / CA9 IHC validation",
        "Spatial O2 mapping if available",
    ],
    FindingType.BIOMARKER: [
        "RT-qPCR for candidate biomarker genes",
        "IF/IHC on independent cohort",
        "Prospective spatial validation cohort",
    ],
    FindingType.CAUSAL_DRIVER: [
        "CRISPR/siRNA perturbation of driver gene",
        "Lineage tracing if driver marks progenitor state",
        "Orthogonal causal inference (e.g. Mendelian randomization)",
    ],
    FindingType.NICHE: [
        "Multiplex spatial imaging (CODEX/IMC) niche confirmation",
        "Neighborhood enrichment on independent slide",
        "Niche-specific laser capture + bulk RNA validation",
    ],
    FindingType.PATHWAY: [
        "RT-qPCR for pathway target genes",
        "Phospho-protein IF for pathway activity",
        "Small-molecule pathway perturbation",
    ],
    FindingType.BENCHMARK: [
        "Independent single-cell reference dataset",
        "Cross-platform validation (Visium vs Xenium)",
        "Hold-out spot reconstruction on unseen tissue section",
    ],
    FindingType.RECONSTRUCTION: [
        "Compare against orthogonal deconvolution method",
        "Spot-level ground truth where available",
        "Marker gene spatial concordance IF",
    ],
}


def recommend_validations(findings: List[Finding]) -> List[Dict[str, Any]]:
    """Return validation suggestions per finding."""
    out: List[Dict[str, Any]] = []
    for finding in findings:
        ftype = finding.finding_type
        recs = _RECOMMENDATIONS.get(ftype, _RECOMMENDATIONS.get(FindingType.BIOMARKER, []))
        if not recs:
            recs = [
                "RT-qPCR validation of top genes",
                "Spatial IF on independent sample",
                "Functional perturbation assay",
            ]
        out.append({
            "finding_id": finding.finding_id,
            "title": finding.title,
            "finding_type": ftype,
            "confidence_level": finding.confidence_level,
            "recommendations": recs,
        })
    return out
