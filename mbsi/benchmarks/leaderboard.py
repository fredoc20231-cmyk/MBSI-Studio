"""Leaderboard aggregation and ranking for benchmark methods."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


RANK_METRICS = [
    ("gene_pearson", False),
    ("gene_spearman", False),
    ("cell_type_accuracy", False),
    ("niche_preservation", False),
    ("boundary_preservation", False),
    ("morans_i_preservation", True),  # lower is better (absolute diff)
    ("rmse", True),
    ("runtime_sec", True),
]


def build_leaderboard(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Rank methods by composite score and individual metrics."""
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df["rank_score"] = 0.0
    for metric, lower_better in RANK_METRICS:
        if metric not in df.columns:
            continue
        vals = pd.to_numeric(df[metric], errors="coerce").fillna(0)
        if lower_better:
            ranks = vals.rank(ascending=True, method="average")
        else:
            ranks = vals.rank(ascending=False, method="average")
        df[f"rank_{metric}"] = ranks
        df["rank_score"] += ranks

    df = df.sort_values("rank_score", ascending=True).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    return df


def leaderboard_summary(leaderboard: pd.DataFrame) -> str:
    """Human-readable summary for CLI / reports."""
    if leaderboard.empty:
        return "No benchmark results."
    lines = ["Benchmark Leaderboard", "=" * 40]
    for _, row in leaderboard.iterrows():
        lines.append(
            f"#{int(row['rank'])} {row['method']} ({row.get('method_type', '?')}) "
            f"pearson={row.get('gene_pearson', 0):.3f} rmse={row.get('rmse', 0):.3f} "
            f"runtime={row.get('runtime_sec', 0):.2f}s"
        )
    return "\n".join(lines)
