"""Tests for mbsi.analysis.seurat_like.qc."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.seurat_like.qc import run_qc, filter_cells_or_spots


def test_run_qc_filters_and_summarizes():
    adata = make_synthetic_visium_adata(n_spots=40, n_genes=100, seed=0)
    filtered, summary, warnings = run_qc(adata, min_counts=0, min_genes=0, max_mito=100)
    assert filtered.n_obs <= adata.n_obs
    assert not summary.empty
    assert "total_counts" in summary["metric"].values


def test_filter_cells_or_spots():
    adata = make_synthetic_visium_adata(n_spots=20, seed=1)
    adata.obs["qc_pass"] = True
    adata.obs.iloc[0, adata.obs.columns.get_loc("qc_pass")] = False
    out = filter_cells_or_spots(adata)
    assert out.n_obs == 19
