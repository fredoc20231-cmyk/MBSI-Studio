"""Visualization helpers for Seurat-like workflow — delegate to mbsi.visualization."""

from __future__ import annotations

from typing import Any, Optional

import anndata as ad

from mbsi.visualization.analysis_plots import (
    plot_spatial_clusters,
    plot_spatial_gene,
    plot_umap,
    plot_qc_violin,
    plot_marker_dotplot,
)
from mbsi.visualization.seurat_like import (
    plot_violin,
    plot_dotplot,
    plot_heatmap,
    plot_umap_split,
)


def spatial_feature_plot(adata: ad.AnnData, gene: str) -> Any:
    return plot_spatial_gene(adata, gene)


def spatial_cluster_plot(adata: ad.AnnData, groupby: str = "cluster") -> Any:
    return plot_spatial_clusters(adata)


def embedding_plot(adata: ad.AnnData, basis: str = "umap", color: Optional[str] = None) -> Any:
    if basis == "umap" and "X_umap" in adata.obsm:
        return plot_umap(adata, color=color or "cluster")
    return None
