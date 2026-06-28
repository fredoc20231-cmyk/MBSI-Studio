"""Normalization and feature selection."""

from __future__ import annotations

import anndata as ad
import numpy as np

from mbsi.utils import to_dense_array


def _as_dense(X) -> np.ndarray:
    return to_dense_array(X)


def normalize_log_transform(adata: ad.AnnData, target_sum: float = 1e4) -> ad.AnnData:
    """Store raw counts, normalize, log1p; layers counts and logcounts."""
    adata = adata.copy()
    adata.layers["counts"] = adata.X.copy()
    X = _as_dense(adata.X).astype(np.float64)
    totals = X.sum(axis=1, keepdims=True)
    X = X / (totals + 1e-12) * target_sum
    X = np.log1p(X)
    adata.X = X
    adata.layers["logcounts"] = X.copy()
    return adata


def select_hvgs(adata: ad.AnnData, n_top_genes: int = 2000) -> ad.AnnData:
    """Mark highly variable genes via per-gene variance."""
    adata = adata.copy()
    X = _as_dense(adata.X)
    n_top = min(n_top_genes, adata.n_vars - 1) if adata.n_vars > 1 else 1
    disp = np.var(X, axis=0)
    order = np.argsort(disp)[::-1]
    hvg = np.zeros(adata.n_vars, dtype=bool)
    hvg[order[:n_top]] = True
    adata.var["highly_variable"] = hvg
    adata.var["dispersions_norm"] = disp
    return adata


def scale_for_pca(adata: ad.AnnData) -> ad.AnnData:
    """Scale data while preserving logcounts layer."""
    adata = adata.copy()
    if "logcounts" in adata.layers:
        X = _as_dense(adata.layers["logcounts"]).astype(np.float64)
    else:
        X = _as_dense(adata.X).astype(np.float64)
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0
    adata.X = (X - mean) / std
    return adata
