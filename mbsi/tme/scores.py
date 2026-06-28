"""TME marker program scoring."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores
from mbsi.tme.marker_sets import TME_MARKER_SETS


def score_marker_programs(adata: ad.AnnData, layer: str = "logcounts") -> pd.DataFrame:
    """Score all TME marker programs per spot/cell."""
    rows = []
    for program, spec in TME_MARKER_SETS.items():
        gene_lists = [v for k, v in spec.items() if k != "label" and isinstance(v, list)]
        if not gene_lists:
            continue
        scores = [get_expression(adata, genes, layer) for genes in gene_lists]
        if len(scores) == 1:
            program_score = normalize_scores(scores[0])
        elif len(scores) == 2:
            program_score = normalize_scores(scores[0] / (scores[1] + 0.5))
        else:
            program_score = normalize_scores(np.mean(scores, axis=0))
        for i, s in enumerate(program_score):
            rows.append({
                "spot": adata.obs_names[i],
                "program": program,
                "label": spec.get("label", program),
                "score": float(s),
            })
    return pd.DataFrame(rows)


def program_summary(program_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate program scores."""
    if program_df.empty:
        return program_df
    return (
        program_df.groupby(["program", "label"], as_index=False)
        .agg(mean_score=("score", "mean"), max_score=("score", "max"), n_spots=("score", "count"))
        .sort_values("mean_score", ascending=False)
    )
