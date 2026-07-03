"""Tests for unified spatial biomarker report."""

from pathlib import Path

from mbsi.reports import (
    generate_spatial_biomarker_report,
    generate_biomarker_report_text,
    BIOMARKER_DISCLAIMER,
)
from mbsi.discovery import run_discovery_engine


def test_biomarker_disclaimer_exact():
    expected = (
        "This report is a computational research output. It is not a diagnostic test, "
        "treatment recommendation, or clinical decision support system. Findings require "
        "independent biological and clinical validation."
    )
    assert BIOMARKER_DISCLAIMER == expected


def test_generate_biomarker_report_text():
    results = run_discovery_engine(seed=42, allow_demo=True)
    text = generate_biomarker_report_text(
        results["benchmark_results"],
        results["communication_results"],
        results["tme_results"],
    )
    assert BIOMARKER_DISCLAIMER in text
    assert "Benchmark Hub" in text
    assert "Communication Intelligence" in text
    assert "TME Intelligence" in text


def test_generate_spatial_biomarker_report_html(tmp_path: Path):
    results = run_discovery_engine(seed=7, allow_demo=True)
    path = generate_spatial_biomarker_report(
        results["benchmark_results"],
        results["communication_results"],
        results["tme_results"],
        tmp_path,
    )
    assert path.exists()
    html = path.read_text()
    assert BIOMARKER_DISCLAIMER in html
    assert (tmp_path / "biomarker_report_summary.json").exists()


def test_report_partial_inputs():
    text = generate_biomarker_report_text(benchmark_results=None, tme_results=None)
    assert BIOMARKER_DISCLAIMER in text
