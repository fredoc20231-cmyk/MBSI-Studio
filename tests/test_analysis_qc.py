"""Tests for mbsi.analysis.qc."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.qc import (
    compute_qc_metrics,
    filter_in_tissue,
    qc_summary_table,
    flag_low_quality_spots,
)


def test_compute_qc_metrics():
    adata = make_synthetic_visium_adata(n_spots=40, n_genes=100, seed=0)
    out = compute_qc_metrics(adata)
    assert "total_counts" in out.obs.columns
    assert "pct_counts_mito" in out.obs.columns
    assert out.obs["total_counts"].min() >= 0


def test_filter_in_tissue():
    adata = make_synthetic_visium_adata(n_spots=20, seed=1)
    adata.obs["in_tissue"] = False
    adata.obs.iloc[:5, adata.obs.columns.get_loc("in_tissue")] = True
    filtered = filter_in_tissue(adata)
    assert filtered.n_obs == 5


def test_qc_summary_table():
    adata = compute_qc_metrics(make_synthetic_visium_adata(n_spots=30, seed=2))
    summary = qc_summary_table(adata)
    assert not summary.empty
    assert set(summary["metric"]) >= {"total_counts", "n_genes_by_counts"}


def test_flag_low_quality_spots():
    adata = compute_qc_metrics(make_synthetic_visium_adata(n_spots=30, seed=3))
    flagged = flag_low_quality_spots(adata, min_counts=0, min_genes=0, max_mito=100)
    assert "qc_pass" in flagged.obs.columns
    assert flagged.obs["qc_pass"].all()
