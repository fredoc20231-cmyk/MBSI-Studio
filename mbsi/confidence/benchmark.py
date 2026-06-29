"""Benchmark-derived support for findings."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.discovery_model.entities import Finding


def benchmark_support_score(
    finding: Finding,
    benchmark_results: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Score 0-25 based on benchmark alignment with finding.

    Reconstruction/benchmark findings get higher support when leaderboard is strong.
    """
    if not benchmark_results:
        return 0.0

    lb = benchmark_results.get("leaderboard")
    top_pearson = 0.0
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        top_pearson = float(lb.iloc[0].get("gene_pearson", 0))

    mode = benchmark_results.get("benchmark_mode", "synthetic")
    base = 5.0 if mode == "synthetic" else 12.0

    if finding.finding_type in ("benchmark", "reconstruction"):
        return min(25.0, base + top_pearson * 15.0)

    if finding.finding_type in ("biomarker", "lr_pathway", "pathway", "niche"):
        return min(20.0, base + top_pearson * 10.0)

    return min(15.0, base + top_pearson * 5.0)
