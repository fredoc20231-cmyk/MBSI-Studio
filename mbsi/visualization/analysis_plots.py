"""Plotly visualizations for spatial analysis (MBSI dark theme)."""

from __future__ import annotations

from typing import Optional

import anndata as ad
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DARK = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
}


def _layout(fig: go.Figure, title: str = "", height: int = 360) -> go.Figure:
    fig.update_layout(
        title=title,
        **DARK,
        height=height,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def plot_qc_spatial(adata: ad.AnnData, metric: str) -> go.Figure:
    coords = adata.obsm["spatial"]
    fig = px.scatter(
        x=coords[:, 0], y=coords[:, 1], color=adata.obs[metric].values,
        color_continuous_scale="Viridis", labels={"color": metric},
    )
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, f"Spatial QC — {metric}")


def plot_qc_violin(adata: ad.AnnData) -> go.Figure:
    metrics = [c for c in ("total_counts", "n_genes_by_counts", "pct_counts_mito") if c in adata.obs.columns]
    fig = go.Figure()
    for m in metrics:
        fig.add_trace(go.Violin(y=adata.obs[m], name=m, box_visible=True))
    return _layout(fig, "QC Violin Plots")


def plot_counts_vs_mito(adata: ad.AnnData) -> go.Figure:
    fig = px.scatter(
        x=adata.obs["total_counts"], y=adata.obs["pct_counts_mito"],
        labels={"x": "Total counts", "y": "% Mito"},
    )
    return _layout(fig, "Counts vs Mitochondrial %")


def plot_pca_elbow(adata: ad.AnnData) -> go.Figure:
    var = adata.uns.get("pca", {}).get("variance_ratio", [])
    fig = go.Figure(data=go.Scatter(x=list(range(1, len(var) + 1)), y=var, mode="lines+markers"))
    fig.update_layout(xaxis_title="PC", yaxis_title="Variance ratio")
    return _layout(fig, "PCA Elbow")


def plot_pca_scatter(adata: ad.AnnData, color: str = "cluster") -> go.Figure:
    pca = adata.obsm["X_pca"]
    c = adata.obs[color].astype(str) if color in adata.obs.columns else None
    fig = px.scatter(x=pca[:, 0], y=pca[:, 1], color=c, labels={"x": "PC1", "y": "PC2"})
    return _layout(fig, f"PCA — {color}")


def plot_umap(adata: ad.AnnData, color: str = "cluster") -> go.Figure:
    umap = adata.obsm["X_umap"]
    c = adata.obs[color].astype(str) if color in adata.obs.columns else None
    fig = px.scatter(x=umap[:, 0], y=umap[:, 1], color=c, labels={"x": "UMAP1", "y": "UMAP2"})
    return _layout(fig, f"UMAP — {color}")


def plot_spatial_clusters(adata: ad.AnnData) -> go.Figure:
    return plot_qc_spatial(adata, "cluster") if "cluster" in adata.obs.columns else plot_qc_spatial(adata, "total_counts")


def plot_spatial_gene(adata: ad.AnnData, gene: str, layer: str = "logcounts") -> go.Figure:
    if gene not in adata.var_names:
        raise ValueError(gene)
    if layer in adata.layers:
        expr = np.asarray(adata[:, gene].layers[layer]).flatten()
    else:
        expr = np.asarray(adata[:, gene].X).flatten()
    coords = adata.obsm["spatial"]
    fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=expr, color_continuous_scale="Inferno")
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, f"Spatial — {gene}")


def plot_marker_dotplot(marker_matrix: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=marker_matrix.values,
        x=marker_matrix.columns.tolist(),
        y=marker_matrix.index.tolist(),
        colorscale=[[0, "#07111f"], [0.5, "#4f7cff"], [1, "#ff5c7a"]],
    ))
    return _layout(fig, "Marker Expression (cluster means)", height=400)


def plot_morans_rank(spatial_stats_df: pd.DataFrame) -> go.Figure:
    df = spatial_stats_df.head(30)
    fig = go.Figure(data=go.Bar(x=df["morans_i"], y=df["gene"], orientation="h"))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _layout(fig, "Top Moran's I")


def plot_gearys_rank(spatial_stats_df: pd.DataFrame) -> go.Figure:
    df = spatial_stats_df.sort_values("gearys_c").head(30)
    fig = go.Figure(data=go.Bar(x=df["gearys_c"], y=df["gene"], orientation="h"))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _layout(fig, "Top Geary's C (low = clustered)")
