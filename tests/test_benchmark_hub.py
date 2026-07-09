"""Tests for Benchmark Hub orchestrator."""

import pytest

pytestmark = pytest.mark.heavy

from mbsi.benchmarks.hub import run_benchmark_hub
from mbsi.benchmarks.leaderboard import build_leaderboard
from mbsi.benchmarks.export import export_benchmark_hub


def test_run_benchmark_hub():
    out = run_benchmark_hub(methods=["mbsi", "tangram"], platform="xenium", seed=42, n_spots=25, synthetic_cells=80)
    assert "leaderboard" in out
    assert len(out["results"]) == 2
    assert not out["leaderboard"].empty
    assert out["leaderboard"].iloc[0]["method"] in ("mbsi", "tangram")


def test_build_leaderboard():
    rows = [
        {"method": "mbsi", "method_type": "full", "gene_pearson": 0.9, "rmse": 0.1, "status": "ok"},
        {"method": "tangram", "method_type": "proxy", "gene_pearson": 0.7, "rmse": 0.2, "status": "ok"},
    ]
    lb = build_leaderboard(rows)
    assert lb.iloc[0]["method"] == "mbsi"


def test_export_benchmark_hub(tmp_path):
    out = run_benchmark_hub(methods=["mbsi"], seed=42, n_spots=20, synthetic_cells=60)
    path = export_benchmark_hub(out, out_dir=tmp_path)
    assert (path / "benchmark_results.csv").exists()
    assert (path / "benchmark_methods.txt").exists()
    assert (path / "benchmark_report.html").exists()
