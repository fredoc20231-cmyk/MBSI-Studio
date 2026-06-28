"""Shared TME helpers.

Delegates to ``mbsi.utils`` for generic operations and re-exports them
so that existing imports from ``mbsi.tme._utils`` keep working.
"""

from __future__ import annotations

from typing import List, Optional

import anndata as ad
import numpy as np

from mbsi.utils import (
    build_knn_graph,
    normalize_scores,
    score_signature,
)

# Re-export so existing ``from mbsi.tme._utils import normalize_scores`` works.
__all__ = ["get_expression", "spatial_smooth", "normalize_scores"]


def get_expression(adata: ad.AnnData, genes: List[str], layer: str = "logcounts") -> np.ndarray:
    """Mean expression of available genes per observation."""
    return score_signature(adata, genes, layer)


def spatial_smooth(coords: np.ndarray, values: np.ndarray, k: int = 8) -> np.ndarray:
    """kNN spatial smoothing."""
    _, idx = build_knn_graph(coords, k=k)
    out = np.zeros_like(values)
    for i in range(len(values)):
        out[i] = values[idx[i]].mean()
    return out
