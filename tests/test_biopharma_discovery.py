"""Tests for Biopharma Discovery Engine orchestrator."""

from pathlib import Path

import pytest

from mbsi.discovery import run_discovery_engine, export_discovery_engine
from mbsi.tme import make_tme_demo_adata
from mbsi.reports import BIOMARKER_DISCLAIMER


def test_run_discovery_engine():
    results = run_discovery_engine(seed=42, allow_demo=True)
    assert "benchmark_results" in results
    assert "communication_results" in results
    assert "tme_results" in results
    assert "actionable_findings" in results
    assert results["disclaimer"] == BIOMARKER_DISCLAIMER
    assert "findings" in results
    assert len(results["findings"]) >= 1
    assert "discovery_graph" in results
    assert len(results["actionable_findings"]) >= 1


def test_discovery_benchmark_readiness():
    results = run_discovery_engine(seed=0, allow_demo=True)
    bench = results["benchmark_results"]
    assert bench.get("readiness_score", 0) >= 60
    assert bench.get("leaderboard") is not None


def test_discovery_communication_top_pathway():
    results = run_discovery_engine(seed=1, allow_demo=True)
    comm = results["communication_results"]
    assert comm.get("top_pathway") is not None
    assert not comm["pathway_rankings"].empty


def test_discovery_tme_programs():
    adata = make_tme_demo_adata(n_spots=80, seed=2)
    results = run_discovery_engine(adata=adata, seed=2)
    tme = results["tme_results"]
    assert "program_scores" in tme
    assert "program_summary" in tme


def test_export_discovery_engine(tmp_path: Path):
    results = run_discovery_engine(seed=3, allow_demo=True)
    export_discovery_engine(results, tmp_path)
    assert (tmp_path / "biopharma_discovery_report.html").exists()
    assert (tmp_path / "discovery_engine_summary.json").exists()
