"""Tests for benchmark hub metrics."""

import anndata as ad
import numpy as np

from mbsi.benchmarks.metrics import compute_benchmark_metrics, compute_niche_preservation
from mbsi.benchmarks.pseudo_visium import make_synthetic_ground_truth


def test_compute_benchmark_metrics():
    gt = make_synthetic_ground_truth(n_cells=60, n_genes=40, seed=0)
    recon = gt.copy()
    recon.X = gt.X + 0.05 * np.random.randn(*gt.X.shape)
    metrics = compute_benchmark_metrics(gt, recon, runtime_sec=1.5, peak_memory_mb=10.0)
    assert "gene_pearson" in metrics
    assert "gene_spearman" in metrics
    assert "rmse" in metrics
    assert metrics["runtime_sec"] == 1.5
    assert metrics["gene_pearson"] > 0.5


def test_compute_niche_preservation():
    gt = make_synthetic_ground_truth(n_cells=50, n_genes=30, seed=1)
    recon = gt.copy()
    score = compute_niche_preservation(gt, recon)
    assert 0.0 <= score <= 1.0
