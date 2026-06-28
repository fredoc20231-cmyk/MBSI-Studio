"""Shared TME helpers."""

from __future__ import annotations

from typing import List, Optional

import anndata as ad
import numpy as np
from sklearn.neighbors import NearestNeighbors


def get_expression(adata: ad.AnnData, genes: List[str], layer: str = "logcounts") -> np.ndarray:
    """Mean expression of available genes per observation."""
    present = [g for g in genes if g in adata.var_names]
    if not present:
        return np.zeros(adata.n_obs)
    if layer in adata.layers:
        X = adata[:, present].layers[layer]
    else:
        X = adata[:, present].X
    X = np.asarray(X.toarray() if hasattr(X, "toarray") else X, dtype=float)
    return X.mean(axis=1)


def spatial_smooth(coords: np.ndarray, values: np.ndarray, k: int = 8) -> np.ndarray:
    """kNN spatial smoothing."""
    k = min(k + 1, len(coords))
    nn = NearestNeighbors(n_neighbors=k).fit(coords)
    _, idx = nn.kneighbors(coords)
    out = np.zeros_like(values)
    for i in range(len(values)):
        out[i] = values[idx[i]].mean()
    return out


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    s = scores.astype(float)
    if s.max() > s.min():
        return (s - s.min()) / (s.max() - s.min())
    return np.zeros_like(s)
