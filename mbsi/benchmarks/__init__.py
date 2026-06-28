"""Benchmarks module for validation and ablation studies."""

from mbsi.benchmarks.pseudo_visium import (
    make_pseudo_visium,
    aggregate_cells_to_spots,
    generate_pseudo_visium,
    make_synthetic_ground_truth,
)
from mbsi.benchmarks.metrics import (
    benchmark_reconstruction,
    compute_all_metrics,
    compute_benchmark_metrics,
)
from mbsi.benchmarks.ablation import run_ablation_suite
from mbsi.benchmarks.competitors import run_baseline_methods
from mbsi.benchmarks.hub import run_benchmark_hub, BENCHMARK_GUARDRAIL, VC_BANNER
from mbsi.benchmarks.leaderboard import build_leaderboard, leaderboard_summary
from mbsi.benchmarks.export import export_benchmark_hub

__all__ = [
    "make_pseudo_visium",
    "aggregate_cells_to_spots",
    "generate_pseudo_visium",
    "make_synthetic_ground_truth",
    "benchmark_reconstruction",
    "compute_all_metrics",
    "compute_benchmark_metrics",
    "run_ablation_suite",
    "run_baseline_methods",
    "run_benchmark_hub",
    "build_leaderboard",
    "leaderboard_summary",
    "export_benchmark_hub",
    "BENCHMARK_GUARDRAIL",
    "VC_BANNER",
]
