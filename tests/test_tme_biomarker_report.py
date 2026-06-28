"""Tests for spatial biomarker report."""

from pathlib import Path

from mbsi.tme import run_tme_analysis, generate_spatial_biomarker_report, make_tme_demo_adata, TME_GUARDRAIL


def test_generate_spatial_biomarker_report(tmp_path: Path):
    results = run_tme_analysis(make_tme_demo_adata(n_spots=70, seed=5))
    path = generate_spatial_biomarker_report(results, tmp_path)
    assert path.exists()
    content = path.read_text()
    assert "Spatial Biomarker Report" in content
    assert TME_GUARDRAIL.split(".")[0] in content
    assert "Immune Exclusion" in content or "immune" in content.lower()


def test_report_contains_biomarkers(tmp_path: Path):
    results = run_tme_analysis(make_tme_demo_adata(n_spots=60, seed=8))
    path = generate_spatial_biomarker_report(results, tmp_path)
    assert "Biomarker" in path.read_text()
