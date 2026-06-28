"""Pathway enrichment for communication results."""

from __future__ import annotations

import pandas as pd


def enrich_pathway_scores(pair_scores: pd.DataFrame) -> pd.DataFrame:
    """Add enrichment rank and category labels to L-R pair scores."""
    if pair_scores.empty:
        return pair_scores
    df = pair_scores.copy()
    df["enrichment_rank"] = df["score"].rank(ascending=False, method="dense").astype(int)
    df["enrichment_percentile"] = df["score"].rank(pct=True)
    category_map = {
        "CXCL12": "chemokine",
        "TGFB1": "immunosuppression",
        "CD274": "checkpoint",
        "VEGFA": "angiogenesis",
        "MIF": "inflammation",
    }
    df["category"] = df["ligand"].map(category_map).fillna("signaling")
    df["hypothesis"] = "computational_hypothesis"
    return df.sort_values("enrichment_rank")
