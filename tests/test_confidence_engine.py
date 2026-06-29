"""Tests for confidence scoring engine."""

from mbsi.confidence.engine import compute_confidence_score, score_finding
from mbsi.discovery_model import Finding, create_evidence


def test_compute_confidence_score_with_evidence():
    finding = Finding.create(
        title="Test",
        summary="Test finding",
        finding_type="benchmark",
        module="benchmark",
    )
    ev1 = create_evidence("benchmark", "metric", "Pearson", value=0.8)
    ev2 = create_evidence("benchmark", "metric", "RMSE", value=0.2)
    score = compute_confidence_score(
        finding, [ev1, ev2],
        benchmark_results={"leaderboard": _mock_lb(), "benchmark_mode": "synthetic"},
        readiness={"score": 80},
    )
    assert 0 <= score <= 100
    assert score >= 30


def test_score_finding_updates_level():
    finding = Finding.create(
        title="Pathway",
        summary="LR pathway",
        finding_type="lr_pathway",
        module="communication",
    )
    ev = create_evidence("communication", "pathway", "CXCL12", value="CXCL12-CXCR4")
    scored = score_finding(finding, [ev], readiness={"score": 70})
    assert scored.confidence_level in ("High", "Moderate", "Exploratory", "Hypothesis")
    assert scored.confidence_score > 0


def _mock_lb():
    import pandas as pd
    return pd.DataFrame([{"method": "mbsi", "gene_pearson": 0.75}])
