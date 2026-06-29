"""Tests for sketch scalability."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.scalability.sketching import compute_sketch, run_sketch_clustering
from mbsi.scalability.memory import estimate_memory
from mbsi.profiles.scalability import should_use_sketch


def test_compute_sketch():
    adata = make_synthetic_visium_adata(n_spots=100, n_genes=50, seed=6)
    sketch = compute_sketch(adata, n=30)
    assert sketch.n_obs == 30


def test_run_sketch_clustering():
    adata = make_synthetic_visium_adata(n_spots=80, n_genes=60, seed=7)
    sketch, note = run_sketch_clustering(adata, sketch_n=40)
    assert "cluster" in sketch.obs.columns


def test_estimate_memory():
    adata = make_synthetic_visium_adata(n_spots=50, n_genes=40, seed=8)
    mem = estimate_memory(adata)
    assert mem["total_gb"] > 0
    assert not should_use_sketch(50)
