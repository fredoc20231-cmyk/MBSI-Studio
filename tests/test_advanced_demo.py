"""Tests for advanced demo script."""

import json
from pathlib import Path


def test_advanced_demo_outputs():
    demo_dir = Path("data/demo/advanced")
    expected = [demo_dir / name for name in ("true_single_cell.h5ad", "pseudo_visium_spots.h5ad", "reconstructed.h5ad", "metrics.json")]
    if not all(p.exists() for p in expected):
        import pytest
        pytest.skip("Advanced demo artifacts are not fully generated in this checkout")
    assert (demo_dir / "true_single_cell.h5ad").exists()
    assert (demo_dir / "pseudo_visium_spots.h5ad").exists()
    assert (demo_dir / "reconstructed.h5ad").exists()
    metrics = json.loads((demo_dir / "metrics.json").read_text())
    assert "pearson_correlation" in metrics
