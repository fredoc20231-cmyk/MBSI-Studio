"""Plotly interactive Seurat-like plots."""

from __future__ import annotations

from typing import Any, List, Optional

import anndata as ad
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.components.theme import apply_plotly_theme


def _apply(fig: go.Figure) -> go.Figure:
    return apply_plotly_theme(fig)


def plot_violin(adata: ad.AnnData, keys: List[str], groupby: str = "cluster") -> go.Figure:
    """Violin plot for QC or gene expression by group."""
    frames = []
    for key in keys:
        if key in adata.obs.columns:
            for grp in adata.obs[groupby].astype(str).unique() if groupby in adata.obs else ["all"]:
                mask = adata.obs[groupby].astype(str) == grp if groupby in adata.obs else np.ones(adata.n_obs, dtype=bool)
                frames.append({"group": grp, "metric": key, "value": adata.obs.loc[mask, key].values})
        elif key in adata.var_names:
            idx = list(adata.var_names).index(key)
            X = adata.X[:, idx]
            if hasattr(X, "toarray"):
                X = X.toarray().flatten()
            for grp in adata.obs[groupby].astype(str).unique():
                mask = adata.obs[groupby].astype(str) == grp
                frames.append({"group": grp, "metric": key, "value": X[mask]})
    df = pd.DataFrame([{"group": f["group"], "metric": f["metric"], "value": v} for f in frames for v in np.atleast_1d(f["value"])])
    if df.empty:
        return _apply(go.Figure())
    fig = px.violin(df, x="group", y="value", color="group", facet_col="metric", box=True, points=False)
    return _apply(fig)


def plot_dotplot(mat: pd.DataFrame, title: str = "Dot plot") -> go.Figure:
    """Dot plot from marker expression matrix (groups × genes)."""
    if mat.empty:
        return _apply(go.Figure())
    melted = mat.reset_index().melt(id_vars="index", var_name="gene", value_name="expression")
    melted.rename(columns={"index": "cluster"}, inplace=True)
    fig = px.scatter(melted, x="gene", y="cluster", size="expression", color="expression", title=title)
    return _apply(fig)


def plot_heatmap(mat: pd.DataFrame, title: str = "Heatmap") -> go.Figure:
    if mat.empty:
        return _apply(go.Figure())
    fig = go.Figure(data=go.Heatmap(z=mat.values, x=list(mat.columns), y=list(mat.index), colorscale="Viridis"))
    fig.update_layout(title=title)
    return _apply(fig)


def plot_ridge(adata: ad.AnnData, gene: str, groupby: str = "cluster") -> go.Figure:
    if gene not in adata.var_names or groupby not in adata.obs.columns:
        return _apply(go.Figure())
    idx = list(adata.var_names).index(gene)
    X = adata.X[:, idx]
    if hasattr(X, "toarray"):
        X = X.toarray().flatten()
    df = pd.DataFrame({"value": X, "group": adata.obs[groupby].astype(str).values})
    fig = px.violin(df, x="value", y="group", orientation="h", title=f"{gene} by {groupby}")
    return _apply(fig)


def plot_spatial_feature(adata: ad.AnnData, feature: str, title: Optional[str] = None) -> go.Figure:
    from mbsi.visualization.analysis_plots import plot_spatial_gene

    if feature in adata.var_names:
        return plot_spatial_gene(adata, feature)
    if feature in adata.obs.columns and "spatial" in adata.obsm:
        coords = adata.obsm["spatial"]
        fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=adata.obs[feature], title=title or feature)
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        return _apply(fig)
    return _apply(go.Figure())


def plot_umap_split(adata: ad.AnnData, split_by: str, basis: str = "umap") -> go.Figure:
    """Faceted UMAP by sample/condition/replicate."""
    key = f"X_{basis}"
    if key not in adata.obsm or split_by not in adata.obs.columns:
        return _apply(go.Figure())
    coords = adata.obsm[key]
    df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "split": adata.obs[split_by].astype(str)})
    if "cluster" in adata.obs.columns:
        df["cluster"] = adata.obs["cluster"].astype(str)
    fig = px.scatter(df, x="x", y="y", color="cluster" if "cluster" in df else None, facet_col="split", title=f"UMAP by {split_by}")
    return _apply(fig)


def plot_marker_map(adata: ad.AnnData, genes: List[str]) -> go.Figure:
    """Multi-panel spatial marker map."""
    genes = [g for g in genes if g in adata.var_names][:4]
    if not genes or "spatial" not in adata.obsm:
        return _apply(go.Figure())
    n = len(genes)
    fig = make_subplots(rows=1, cols=n, subplot_titles=genes)
    coords = adata.obsm["spatial"]
    for i, gene in enumerate(genes):
        idx = list(adata.var_names).index(gene)
        vals = adata.X[:, idx]
        if hasattr(vals, "toarray"):
            vals = vals.toarray().flatten()
        fig.add_trace(go.Scatter(x=coords[:, 0], y=coords[:, 1], mode="markers", marker=dict(color=vals, colorscale="Viridis", size=4), name=gene), row=1, col=i + 1)
    return _apply(fig)
