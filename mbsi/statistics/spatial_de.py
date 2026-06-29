"""Spatial differential expression."""

from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def run_spatial_de(
    adata: ad.AnnData,
    n_top: int = 500,
    method: str = "morans_proxy",
) -> pd.DataFrame:
    """Identify spatially variable genes via variance / local Moran's proxy."""
    if "spatial" not in adata.obsm:
        return pd.DataFrame()

    X = adata.X
    if hasattr(X, "toarray"):
        X = X.toarray()
    coords = adata.obsm["spatial"]
    from sklearn.neighbors import NearestNeighbors

    nn = NearestNeighbors(n_neighbors=min(6, adata.n_obs)).fit(coords)
    _, idx = nn.kneighbors(coords)
    rows = []
    n_genes = min(n_top, adata.n_vars)
    gene_var = np.var(X, axis=0)
    top_idx = np.argsort(gene_var)[::-1][:n_genes]
    for gi in top_idx:
        vals = X[:, gi]
        local_mean = vals[idx].mean(axis=1)
        corr = np.corrcoef(vals, local_mean)[0, 1] if np.std(vals) > 0 else 0.0
        rows.append({
            "gene": adata.var_names[gi],
            "spatial_score": float(corr),
            "variance": float(gene_var[gi]),
            "method": method,
        })
    df = pd.DataFrame(rows).sort_values("spatial_score", ascending=False)
    return df
