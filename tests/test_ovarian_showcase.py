"""Tests for Ovarian HGSOC showcase."""

from pathlib import Path

from mbsi.showcase import (
    make_ovarian_showcase_adata,
    run_ovarian_showcase_pipeline,
    export_ovarian_showcase,
    generate_ovarian_showcase_report,
    SHOWCASE_GUARDRAIL,
)


def test_make_ovarian_showcase_adata():
    adata = make_ovarian_showcase_adata(n_spots=80, seed=42)
    assert adata.n_obs == 80
    assert "CXCL12" in adata.var_names
    assert "cell_type" in adata.obs.columns
    assert adata.uns["disease"] == "HGSOC"


def test_run_ovarian_showcase_pipeline():
    results = run_ovarian_showcase_pipeline(seed=42)
    assert "findings" in results
    assert "caf_barrier_niches" in results["findings"]
    assert "cxcl12_signaling_regions" in results["findings"]
    assert "immune_excluded_tumor_fronts" in results["findings"]
    assert "platinum_resistance_microenvironments" in results["findings"]
    assert results["findings"]["caf_barrier_niches"]["hypothesis"] == "computational_hypothesis"
    assert "communication" in results
    assert "tme" in results


def test_export_and_report(tmp_path: Path):
    results = run_ovarian_showcase_pipeline(seed=42)
    export_ovarian_showcase(results, tmp_path)
    report = generate_ovarian_showcase_report(results, tmp_path)
    assert report.exists()
    assert (tmp_path / "ovarian_showcase_biomarkers.csv").exists()
    assert (tmp_path / "ovarian_showcase_summary.json").exists()
    content = report.read_text()
    assert "High-Grade Serous Ovarian Cancer" in content
    assert SHOWCASE_GUARDRAIL.split(".")[0] in content
    assert "CAF barrier" in content or "caf_barrier" in content.lower()
