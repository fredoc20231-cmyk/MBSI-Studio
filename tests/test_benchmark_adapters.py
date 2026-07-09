"""Tests for benchmark adapters."""

import pytest

pytestmark = pytest.mark.heavy

from mbsi.benchmarks.adapters import get_adapter, list_adapters
from mbsi.benchmarks.pseudo_visium import make_synthetic_ground_truth, generate_pseudo_visium


def test_list_adapters():
    names = list_adapters()
    assert "mbsi" in names
    assert "tangram" in names


def test_mbsi_adapter():
    gt = make_synthetic_ground_truth(n_cells=80, n_genes=40, seed=0)
    pseudo = generate_pseudo_visium(gt, n_spots=25, seed=0)
    adapter = get_adapter("mbsi")
    result = adapter.run(gt, pseudo)
    assert result.method_type == "full"
    assert result.reconstructed_adata.n_obs > 0


def test_proxy_adapter():
    gt = make_synthetic_ground_truth(n_cells=60, n_genes=30, seed=1)
    pseudo = generate_pseudo_visium(gt, n_spots=20, seed=1)
    result = get_adapter("tangram").run(gt, pseudo)
    assert result.method_type == "proxy"
    assert "baseline_proxy" in result.notes or "proxy" in result.notes.lower()
