"""Confidence scoring rules for Discovery OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.discovery_model.entities import Evidence, Finding


def evidence_count_score(evidence_list: List[Evidence]) -> float:
    """More independent evidence sources increase confidence."""
    n = len(evidence_list)
    if n >= 4:
        return 25.0
    if n >= 2:
        return 15.0
    if n >= 1:
        return 8.0
    return 0.0


def agreement_score(finding: Finding, evidence_list: List[Evidence]) -> float:
    """Score agreement across evidence values (e.g. consistent metrics)."""
    numeric = [e.value for e in evidence_list if isinstance(e.value, (int, float))]
    if len(numeric) < 2:
        return 5.0 if numeric else 0.0
    spread = max(numeric) - min(numeric)
    if spread <= 0.1:
        return 20.0
    if spread <= 0.3:
        return 12.0
    return 5.0


def data_quality_score(readiness: Optional[Dict[str, Any]]) -> float:
    """Incorporate mbsi_readiness from ingestion."""
    if not readiness:
        return 5.0
    score = readiness.get("score") or readiness.get("readiness_score")
    if score is None:
        return 5.0
    return min(25.0, float(score) * 0.25)


def finding_type_prior(finding_type: str) -> float:
    """Base prior by finding category."""
    priors = {
        "benchmark": 10.0,
        "reconstruction": 10.0,
        "lr_pathway": 8.0,
        "pathway": 8.0,
        "biomarker": 12.0,
        "niche": 10.0,
        "immune_exclusion": 8.0,
        "hypoxia_niche": 8.0,
        "causal_driver": 5.0,
    }
    return priors.get(finding_type, 6.0)
