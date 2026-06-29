"""Confidence scoring engine for Discovery OS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.confidence.benchmark import benchmark_support_score
from mbsi.confidence.rules import (
    agreement_score,
    data_quality_score,
    evidence_count_score,
    finding_type_prior,
)
from mbsi.discovery_model.confidence import confidence_level
from mbsi.discovery_model.entities import Evidence, Finding


def compute_confidence_score(
    finding: Finding,
    evidence_list: List[Evidence],
    benchmark_results: Optional[Dict[str, Any]] = None,
    readiness: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Compute 0-100 confidence score from evidence, agreement, data quality, benchmark.

    Components:
    - evidence count (0-25)
    - agreement (0-20)
    - data quality from mbsi_readiness (0-25)
    - benchmark support (0-25)
    - finding type prior (0-5)
    """
    score = (
        evidence_count_score(evidence_list)
        + agreement_score(finding, evidence_list)
        + data_quality_score(readiness)
        + benchmark_support_score(finding, benchmark_results)
        + finding_type_prior(finding.finding_type)
    )
    return round(min(100.0, max(0.0, score)), 1)


def score_finding(
    finding: Finding,
    evidence_list: List[Evidence],
    benchmark_results: Optional[Dict[str, Any]] = None,
    readiness: Optional[Dict[str, Any]] = None,
) -> Finding:
    """Update finding with computed confidence score and level."""
    finding.confidence_score = compute_confidence_score(
        finding, evidence_list, benchmark_results, readiness
    )
    finding.confidence_level = confidence_level(finding.confidence_score)
    return finding
