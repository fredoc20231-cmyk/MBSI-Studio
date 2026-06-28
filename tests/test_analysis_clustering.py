"""Tests for mbsi.analysis.clustering."""

from mbsi.analysis.clustering import (
    run_pca,
    run_neighbors,
    run_leiden_clustering,
    run_umap,
    full_clustering_workflow,
)
from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.preprocessing import normalize_log_transform, select_hvgs, scale_for_pca


def _prepped(n_spots=60, n_genes=120):
    adata = make_synthetic_visium_adata(n_spots=n_spots, n_genes=n_genes, seed=7)
    adata = normalize_log_transform(adata)
    adata = select_hvgs(adata, n_top_genes=80)
    return scale_for_pca(adata)


def test_run_pca():
    adata = run_pca(_prepped(), n_comps=10)
    assert "X_pca" in adata.obsm
    assert adata.obsm["X_pca"].shape[1] == 10


def test_run_neighbors_and_leiden():
    adata = run_pca(_prepped(), n_comps=10)
    adata = run_neighbors(adata, n_neighbors=10, n_pcs=5)
    adata = run_leiden_clustering(adata, resolution=0.8)
    assert "cluster" in adata.obs.columns
    assert adata.obs["cluster"].nunique() >= 1


def test_run_umap():
    adata = run_pca(_prepped(), n_comps=10)
    adata = run_neighbors(adata, n_neighbors=10, n_pcs=5)
    adata = run_umap(adata)
    assert "X_umap" in adata.obsm


def test_full_clustering_workflow():
    adata = full_clustering_workflow(
        make_synthetic_visium_adata(n_spots=50, n_genes=100, seed=9),
        n_top_genes=60,
        n_comps=10,
        n_neighbors=10,
        n_pcs=5,
        resolution=0.8,
    )
    assert "cluster" in adata.obs.columns
    assert "X_umap" in adata.obsm
