"""Tests for mbsi.analysis.seurat_like clustering."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.seurat_like.clustering import run_leiden, run_louvain
from mbsi.analysis.seurat_like.reduction import run_pca, run_neighbors, scale_data
from mbsi.analysis.seurat_like.normalization import normalize_log1p
from mbsi.analysis.seurat_like.variable_features import find_variable_features


def _prepped():
    adata = make_synthetic_visium_adata(n_spots=50, n_genes=100, seed=3)
    adata = normalize_log1p(adata)
    adata = find_variable_features(adata, n_top_genes=50)
    adata = scale_data(adata)
    adata = run_pca(adata, n_comps=10)
    return run_neighbors(adata, n_neighbors=10, n_pcs=5)


def test_run_leiden():
    adata, note = run_leiden(_prepped(), resolution=0.8)
    assert "cluster" in adata.obs.columns
    assert adata.obs["cluster"].nunique() >= 1


def test_run_louvain_fallback():
    adata, note = run_louvain(_prepped(), resolution=0.8)
    assert "cluster" in adata.obs.columns
    assert note  # honest fallback note
