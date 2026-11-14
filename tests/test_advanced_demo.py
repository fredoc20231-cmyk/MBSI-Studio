"""Validate optional developer-only advanced demo artifacts when generated.

Synthetic demo files are intentionally not committed and are not a prerequisite
for real-data CI. A missing demo must skip instead of failing production tests.
"""
import json
from pathlib import Path

import pytest


def test_advanced_demo_outputs():
    demo_dir = Path("data/demo/advanced")
    required = [
        demo_dir / "true_single_cell.h5ad",
        demo_dir / "pseudo_visium_spots.h5ad",
        demo_dir / "reconstructed.h5ad",
        demo_dir / "metrics.json",
    ]
    if not all(path.exists() for path in required):
        pytest.skip("Optional synthetic demo artifacts have not been generated")
    metrics = json.loads((demo_dir / "metrics.json").read_text())
    assert "pearson_correlation" in metrics
