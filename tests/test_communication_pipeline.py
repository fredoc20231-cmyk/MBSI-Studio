"""Tests for full communication pipeline."""

import pytest

pytestmark = pytest.mark.heavy

from pathlib import Path

from mbsi.communication import (
    run_communication_analysis,
    export_communication_results,
    make_communication_demo_adata,
)


def test_run_communication_analysis():
    adata = make_communication_demo_adata(n_spots=60, seed=42)
    results = run_communication_analysis(adata, k=5)
    assert "pathway_rankings" in results
    assert "pair_scores" in results
    assert results["top_pathway"] is not None
    assert results["hypothesis_label"] == "computational_hypothesis"
    assert not results["pathway_rankings"].empty


def test_export_communication_results(tmp_path: Path):
    adata = make_communication_demo_adata(n_spots=40, seed=7)
    results = run_communication_analysis(adata, k=4)
    export_communication_results(results, tmp_path)
    assert (tmp_path / "communication_pairs.csv").exists()
    assert (tmp_path / "pathway_rankings.csv").exists()
    assert (tmp_path / "sender_receiver.csv").exists()
