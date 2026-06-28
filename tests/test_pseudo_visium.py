"""Tests for pseudo-Visium generation."""

from mbsi.benchmarks.pseudo_visium import (
    make_synthetic_ground_truth,
    generate_pseudo_visium,
    make_pseudo_visium,
)


def test_make_synthetic_ground_truth():
    gt = make_synthetic_ground_truth(n_cells=100, n_genes=50, seed=0)
    assert gt.n_obs == 100
    assert gt.n_vars == 50
    assert "spatial" in gt.obsm
    assert "cell_type" in gt.obs.columns


def test_generate_pseudo_visium():
    gt = make_synthetic_ground_truth(n_cells=120, n_genes=40, seed=1)
    pseudo = generate_pseudo_visium(gt, n_spots=30, platform="xenium", seed=1)
    assert pseudo.n_obs <= 30
    assert pseudo.n_vars == gt.n_vars
    assert pseudo.uns["platform"] == "xenium"


def test_make_pseudo_visium_hex():
    gt = make_synthetic_ground_truth(n_cells=80, n_genes=30, seed=2)
    pseudo = make_pseudo_visium(gt, n_spots=20, aggregation="hex", random_state=2)
    assert pseudo.n_obs <= 20
    assert "spatial" in pseudo.obsm
