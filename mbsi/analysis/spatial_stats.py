"""Spatial autocorrelation (Moran's I, Geary's C) via kNN weights."""

from __future__ import annotations

from typing import List, Optional

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from mbsi.utils import build_knn_graph


def build_spatial_weights(adata: ad.AnnData, k: int = 6) -> sparse.csr_matrix:
    """Build symmetric kNN spatial weights from obsm['spatial']."""
    coords = np.asarray(adata.obsm["spatial"])
    n = coords.shape[0]
    _, indices = build_knn_graph(coords, k=k)

    rows, cols, data = [], [], []
    for i in range(n):
        for j in indices[i]:
            if i == j:
                continue
            rows.extend([i, j])
            cols.extend([j, i])
            data.extend([1.0, 1.0])
    W = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    W = W.maximum(W.T)
    return W


def _get_expression(adata: ad.AnnData, gene: str, layer: str) -> np.ndarray:
    if layer in adata.layers:
        x = adata[:, gene].layers[layer]
    else:
        x = adata[:, gene].X
    return np.asarray(x).flatten().astype(float)


def morans_i(adata: ad.AnnData, genes: List[str], k: int = 6, layer: str = "logcounts") -> pd.DataFrame:
    """Compute Moran's I per gene."""
    W = build_spatial_weights(adata, k=k)
    n = adata.n_obs
    S0 = W.sum()
    rows = []
    for gene in genes:
        if gene not in adata.var_names:
            continue
        x = _get_expression(adata, gene, layer)
        xc = x - x.mean()
        denom = np.dot(xc, xc) + 1e-12
        num = float(xc @ (W @ xc))
        I = (n / S0) * (num / denom)
        rows.append({"gene": gene, "morans_i": I})
    return pd.DataFrame(rows)


def gearys_c(adata: ad.AnnData, genes: List[str], k: int = 6, layer: str = "logcounts") -> pd.DataFrame:
    """Compute Geary's C per gene."""
    W = build_spatial_weights(adata, k=k)
    n = adata.n_obs
    S0 = W.sum()
    rows = []
    W_coo = W.tocoo()
    for gene in genes:
        if gene not in adata.var_names:
            continue
        x = _get_expression(adata, gene, layer)
        xc = x - x.mean()
        denom = np.dot(xc, xc) + 1e-12
        num = 0.0
        for i, j, w in zip(W_coo.row, W_coo.col, W_coo.data):
            num += w * (x[i] - x[j]) ** 2
        C = ((n - 1) / (2 * S0)) * (num / denom)
        rows.append({"gene": gene, "gearys_c": C})
    return pd.DataFrame(rows)


def spatial_autocorrelation_table(
    adata: ad.AnnData,
    genes: Optional[List[str]] = None,
    n_top: int = 2000,
    k: int = 6,
    layer: str = "logcounts",
) -> pd.DataFrame:
    """Compute Moran's I and Geary's C for genes; return ranked dataframe."""
    if genes is None:
        if "highly_variable" in adata.var.columns:
            genes = adata.var_names[adata.var["highly_variable"]].tolist()
        else:
            genes = adata.var_names.tolist()
    genes = genes[:n_top]

    mi = morans_i(adata, genes, k=k, layer=layer)
    gc = gearys_c(adata, genes, k=k, layer=layer)
    df = mi.merge(gc, on="gene", how="outer")
    df = df.sort_values("morans_i", ascending=False).reset_index(drop=True)
    return df
