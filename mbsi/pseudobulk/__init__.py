"""Pseudobulk aggregation, PCA, and heatmap."""

from __future__ import annotations

from typing import List, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd

def aggregate_by(
    adata: ad.AnnData,
    groupby: str,
    layer: str = "logcounts",
) -> pd.DataFrame:
    """Aggregate expression matrix by obs column (mean)."""
    if groupby not in adata.obs.columns:
        return pd.DataFrame()
    X = adata.layers[layer] if layer in adata.layers else adata.X
    if hasattr(X, "toarray"):
        X = X.toarray()
    X = np.asarray(X, dtype=float)
    groups = adata.obs[groupby].astype(str)
    rows = {}
    for g in groups.unique():
        mask = groups == g
        rows[g] = X[mask].mean(axis=0)
    return pd.DataFrame(rows, index=adata.var_names).T


def run_pca_heatmap(
    adata: ad.AnnData,
    groupby: str = "condition",
    n_components: int = 2,
    layer: str = "logcounts",
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[object]]:
    """Return (pseudobulk matrix, PCA coords, heatmap figure)."""
    mat = aggregate_by(adata, groupby, layer=layer)
    if mat.empty or mat.shape[0] < 2:
        return mat, pd.DataFrame(), None

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    X = StandardScaler().fit_transform(mat.values)
    n_comp = min(n_components, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_comp)
    coords = pca.fit_transform(X)
    pca_df = pd.DataFrame(coords, index=mat.index, columns=[f"PC{i+1}" for i in range(n_comp)])

    try:
        import plotly.graph_objects as go
        from app.components.theme import apply_plotly_theme

        fig = go.Figure(data=go.Heatmap(z=mat.values, x=list(mat.columns), y=list(mat.index), colorscale="Viridis"))
        fig.update_layout(title=f"Pseudobulk heatmap by {groupby}")
        fig = apply_plotly_theme(fig)
    except Exception:
        fig = None

    return mat, pca_df, fig
