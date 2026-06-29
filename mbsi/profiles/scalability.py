"""Backed/sketch thresholds and config for large datasets."""

from __future__ import annotations

from typing import Any, Dict

SCALABILITY_CONFIG: Dict[str, Any] = {
    "sketch_threshold_n_obs": 50_000,
    "backed_threshold_n_obs": 100_000,
    "sketch_default_n": 10_000,
    "sketch_max_n": 50_000,
    "chunk_size": 5000,
    "memory_warning_gb": 8.0,
    "large_dataset_message": "Large dataset detected — using sketch/backed mode.",
}


def get_scalability_config() -> Dict[str, Any]:
    return dict(SCALABILITY_CONFIG)


def should_use_sketch(n_obs: int, threshold: int | None = None) -> bool:
    threshold = threshold or SCALABILITY_CONFIG["sketch_threshold_n_obs"]
    return n_obs >= threshold


def should_use_backed(n_obs: int, threshold: int | None = None) -> bool:
    threshold = threshold or SCALABILITY_CONFIG["backed_threshold_n_obs"]
    return n_obs >= threshold


def scalability_mode(n_obs: int) -> str:
    if should_use_backed(n_obs):
        return "backed"
    if should_use_sketch(n_obs):
        return "sketch"
    return "in_memory"
