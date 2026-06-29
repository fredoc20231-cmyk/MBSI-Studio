"""Dimensionality reduction for Seurat-like workflow."""

from __future__ import annotations

import anndata as ad

from mbsi.analysis.clustering import run_neighbors as _run_neighbors
from mbsi.analysis.clustering import run_pca as _run_pca
from mbsi.analysis.clustering import run_umap as _run_umap
from mbsi.analysis.preprocessing import scale_for_pca


def scale_data(adata: ad.AnnData) -> ad.AnnData:
    """Scale data for PCA; delegates to mbsi.analysis.preprocessing."""
    return scale_for_pca(adata)


def run_pca(adata: ad.AnnData, n_comps: int = 30, use_highly_variable: bool = True) -> ad.AnnData:
    return _run_pca(adata, n_comps=n_comps, use_highly_variable=use_highly_variable)


def run_neighbors(adata: ad.AnnData, n_neighbors: int = 30, n_pcs: int = 15) -> ad.AnnData:
    return _run_neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)


def run_umap(adata: ad.AnnData, n_pcs: int = 15) -> ad.AnnData:
    return _run_umap(adata, n_pcs=n_pcs)


def run_tsne(adata: ad.AnnData, n_pcs: int = 15, perplexity: float = 30.0) -> ad.AnnData:
    """Run t-SNE on PCA embedding."""
    adata = adata.copy()
    if "X_pca" not in adata.obsm:
        raise ValueError("Run PCA before t-SNE")
    from sklearn.manifold import TSNE

    n_pcs = min(n_pcs, adata.obsm["X_pca"].shape[1])
    perp = min(perplexity, adata.n_obs - 1)
    tsne = TSNE(n_components=2, random_state=0, perplexity=max(5, perp))
    adata.obsm["X_tsne"] = tsne.fit_transform(adata.obsm["X_pca"][:, :n_pcs])
    return adata
