"""Tests for mbsi.analysis.preprocessing."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.preprocessing import normalize_log_transform, select_hvgs, scale_for_pca


def test_normalize_log_transform():
    adata = make_synthetic_visium_adata(n_spots=30, n_genes=80, seed=0)
    out = normalize_log_transform(adata)
    assert "counts" in out.layers
    assert "logcounts" in out.layers


def test_select_hvgs():
    adata = normalize_log_transform(make_synthetic_visium_adata(n_spots=40, n_genes=120, seed=1))
    out = select_hvgs(adata, n_top_genes=50)
    assert "highly_variable" in out.var.columns
    assert out.var["highly_variable"].sum() <= 50


def test_scale_for_pca():
    adata = select_hvgs(
        normalize_log_transform(make_synthetic_visium_adata(n_spots=30, n_genes=80, seed=2)),
        n_top_genes=40,
    )
    out = scale_for_pca(adata)
    assert "logcounts" in out.layers
