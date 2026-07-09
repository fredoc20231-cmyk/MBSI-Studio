"""Tests for end-to-end analysis pipeline."""

import pytest

pytestmark = pytest.mark.heavy

from pathlib import Path

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.pipeline import (
    run_standard_spatial_analysis,
    export_analysis_results,
    ANALYSIS_GUARDRAIL,
)


def test_run_standard_spatial_analysis():
    adata = make_synthetic_visium_adata(n_spots=80, n_genes=150, seed=11)
    results = run_standard_spatial_analysis(
        adata,
        min_counts=0,
        min_genes=0,
        max_mito=100.0,
        n_top_genes=80,
        n_comps=10,
        n_neighbors=10,
        n_pcs=5,
        resolution=0.8,
        spatial_stats_top_n=30,
    )
    assert results["adata"].n_obs > 0
    assert "cluster" in results["adata"].obs.columns
    assert not results["qc_summary"].empty
    assert not results["markers"].empty
    assert not results["spatial_stats"].empty
    assert results["guardrail"] == ANALYSIS_GUARDRAIL


def test_export_analysis_results(tmp_path: Path):
    adata = make_synthetic_visium_adata(n_spots=60, n_genes=100, seed=12)
    results = run_standard_spatial_analysis(
        adata,
        min_counts=0,
        min_genes=0,
        max_mito=100.0,
        n_top_genes=60,
        n_comps=8,
        n_neighbors=10,
        n_pcs=5,
        spatial_stats_top_n=20,
    )
    out = export_analysis_results(results, out_dir=tmp_path)
    for fname in (
        "qc_summary.csv",
        "cluster_markers.csv",
        "spatial_autocorrelation.csv",
        "processed_adata.h5ad",
        "analysis_parameters.json",
    ):
        assert (out / fname).exists()
