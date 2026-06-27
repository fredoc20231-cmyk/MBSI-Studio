"""Tests for advanced demo script."""

import json
from pathlib import Path


def test_advanced_demo_outputs():
    demo_dir = Path("data/demo/advanced")
    if not demo_dir.exists():
        return  # skip if demo not run
    assert (demo_dir / "true_single_cell.h5ad").exists()
    assert (demo_dir / "pseudo_visium_spots.h5ad").exists()
    assert (demo_dir / "reconstructed.h5ad").exists()
    metrics = json.loads((demo_dir / "metrics.json").read_text())
    assert "pearson_correlation" in metrics
