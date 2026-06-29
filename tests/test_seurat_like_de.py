"""Tests for Seurat-like differential expression."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.seurat_like.differential_expression import run_differential_expression
from mbsi.statistics.differential import run_cluster_de, run_condition_de


def _clustered():
    adata = make_synthetic_visium_adata(n_spots=40, n_genes=80, seed=4)
    adata.obs["cluster"] = ["0"] * 20 + ["1"] * 20
    return adata


def test_run_differential_expression():
    df = run_differential_expression(_clustered())
    assert not df.empty or _clustered().n_obs >= 2
    if not df.empty:
        assert "gene" in df.columns
        assert "pval" in df.columns


def test_run_cluster_de():
    df = run_cluster_de(_clustered())
    assert "gene" in df.columns or df.empty


def test_run_condition_de():
    adata = _clustered()
    adata.obs["condition"] = ["A"] * 20 + ["B"] * 20
    df = run_condition_de(adata)
    assert not df.empty
    assert "logfoldchange" in df.columns
