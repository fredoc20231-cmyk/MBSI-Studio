"""Scalability utilities for large datasets."""

from __future__ import annotations

from typing import Any, Dict

import anndata as ad


def estimate_memory(adata: ad.AnnData) -> Dict[str, Any]:
    """Estimate memory footprint in GB."""
    n_obs, n_vars = adata.n_obs, adata.n_vars
    matrix_gb = (n_obs * n_vars * 8) / (1024**3)
    obs_gb = adata.obs.memory_usage(deep=True).sum() / (1024**3)
    return {
        "n_obs": n_obs,
        "n_vars": n_vars,
        "matrix_gb": float(matrix_gb),
        "obs_gb": float(obs_gb),
        "total_gb": float(matrix_gb + obs_gb),
    }
