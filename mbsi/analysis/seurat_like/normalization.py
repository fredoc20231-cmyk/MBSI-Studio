"""Normalization for Seurat-like workflow."""

from __future__ import annotations

from typing import Tuple

import anndata as ad
import numpy as np

from mbsi.analysis.preprocessing import normalize_log_transform


def normalize_log1p(adata: ad.AnnData, target_sum: float = 1e4) -> ad.AnnData:
    """Log-normalize counts; delegates to mbsi.analysis.preprocessing."""
    return normalize_log_transform(adata, target_sum=target_sum)


def _pearson_residuals(X: np.ndarray) -> Tuple[np.ndarray, str]:
    """Approximate SCTransform via Pearson residuals on log-normalized data."""
    X = X.astype(np.float64)
    totals = X.sum(axis=1, keepdims=True)
    X_norm = X / (totals + 1e-12) * 1e4
    mu = X_norm.mean(axis=0, keepdims=True)
    var = X_norm.var(axis=0, keepdims=True) + 1e-12
    residuals = (X_norm - mu) / np.sqrt(var)
    return residuals, "Pearson residuals approximation (full SCTransform unavailable)"


def run_sctransform_like(adata: ad.AnnData) -> Tuple[ad.AnnData, str]:
    """SCTransform-like normalization with scanpy/scvi fallback or Pearson residuals."""
    adata = adata.copy()
    adata.layers["counts"] = adata.X.copy()
    note = ""

    try:
        import scanpy as sc

        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)
        try:
            sc.experimental.pp.recipe_pearson_residuals(adata, n_top_genes=min(3000, adata.n_vars - 1))
            note = "Scanpy Pearson residuals recipe"
            return adata, note
        except Exception:
            pass
    except ImportError:
        pass

    X = adata.X
    if hasattr(X, "toarray"):
        X = X.toarray()
    residuals, note = _pearson_residuals(np.asarray(X))
    adata.X = residuals
    adata.layers["sctransform_like"] = residuals.copy()
    return adata, note
