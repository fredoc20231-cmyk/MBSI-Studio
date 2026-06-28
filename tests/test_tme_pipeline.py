"""Tests for TME pipeline."""

from pathlib import Path

from mbsi.tme import run_tme_analysis, export_tme_results, make_tme_demo_adata


def test_run_tme_analysis():
    results = run_tme_analysis(make_tme_demo_adata(n_spots=80, seed=42))
    assert "niches" in results
    assert len(results["niches"]) == 6
    assert not results["summary"].empty
    assert "immune_exclusion" in results["niches"]
    assert "invasive_fronts" in results["niches"]


def test_all_niche_types_detected():
    results = run_tme_analysis(make_tme_demo_adata(n_spots=100, seed=7))
    expected = {"immune_exclusion", "tls_like", "caf_barriers", "hypoxic", "angiogenic", "invasive_fronts"}
    assert set(results["niches"].keys()) == expected


def test_export_tme_results(tmp_path: Path):
    results = run_tme_analysis(make_tme_demo_adata(n_spots=60, seed=3))
    export_tme_results(results, tmp_path)
    assert (tmp_path / "tme_niches.csv").exists()
    assert (tmp_path / "tme_scores.csv").exists()
