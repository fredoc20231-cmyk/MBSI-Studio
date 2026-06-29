"""Sketch-based analysis for large datasets."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import anndata as ad
import numpy as np

from mbsi.analysis.seurat_like.clustering import run_leiden
from mbsi.analysis.seurat_like.reduction import run_neighbors, run_pca, scale_data
from mbsi.analysis.seurat_like.normalization import normalize_log1p
from mbsi.analysis.seurat_like.variable_features import find_variable_features


def compute_sketch(adata: ad.AnnData, n: int = 10000, seed: int = 0) -> ad.AnnData:
    """Random subsample for sketch analysis."""
    n = min(n, adata.n_obs)
    rng = np.random.default_rng(seed)
    idx = rng.choice(adata.n_obs, size=n, replace=False)
    return adata[idx].copy()


def run_sketch_pca(adata: ad.AnnData, sketch_n: int = 10000, n_comps: int = 30) -> Tuple[ad.AnnData, ad.AnnData]:
    """Run PCA on sketch; return (sketch_adata, full_adata with loadings)."""
    sketch = compute_sketch(adata, n=sketch_n)
    sketch = normalize_log1p(sketch)
    sketch = find_variable_features(sketch)
    sketch = scale_data(sketch)
    sketch = run_pca(sketch, n_comps=n_comps)
    return sketch, adata


def run_sketch_clustering(
    adata: ad.AnnData,
    sketch_n: int = 10000,
    resolution: float = 1.0,
) -> Tuple[ad.AnnData, str]:
    """Cluster on sketch subset."""
    sketch = compute_sketch(adata, n=sketch_n)
    sketch = normalize_log1p(sketch)
    sketch = find_variable_features(sketch)
    sketch = scale_data(sketch)
    sketch = run_pca(sketch)
    sketch = run_neighbors(sketch)
    sketch, note = run_leiden(sketch, resolution=resolution)
    return sketch, note


def project_full_dataset(sketch: ad.AnnData, full: ad.AnnData) -> ad.AnnData:
    """Project sketch cluster labels to full dataset via nearest neighbors in PCA space."""
    from sklearn.neighbors import NearestNeighbors

    full = full.copy()
    if "X_pca" not in sketch.obsm:
        return full
    sketch_pca = sketch.obsm["X_pca"]
    full = normalize_log1p(full)
    full = find_variable_features(full, n_top_genes=int(sketch.var["highly_variable"].sum()) if "highly_variable" in sketch.var else 2000)
    full = scale_data(full)
    full = run_pca(full, n_comps=sketch_pca.shape[1])
    nn = NearestNeighbors(n_neighbors=1).fit(sketch_pca)
    _, idx = nn.kneighbors(full.obsm["X_pca"])
    if "cluster" in sketch.obs.columns:
        full.obs["cluster"] = sketch.obs["cluster"].iloc[idx.flatten()].values
    return full
