"""Benchmarks module for validation and ablation studies."""

from mbsi.benchmarks.pseudo_visium import make_pseudo_visium, aggregate_cells_to_spots
from mbsi.benchmarks.metrics import benchmark_reconstruction, compute_all_metrics
from mbsi.benchmarks.ablation import run_ablation_suite
from mbsi.benchmarks.competitors import run_baseline_methods

__all__ = [
    "make_pseudo_visium",
    "aggregate_cells_to_spots",
    "benchmark_reconstruction",
    "compute_all_metrics",
    "run_ablation_suite",
    "run_baseline_methods"
]
