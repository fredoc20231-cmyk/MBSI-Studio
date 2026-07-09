"""Tests for StarDist nuclei segmentation pipeline."""

from __future__ import annotations

import numpy as np
import pytest

stardist = pytest.importorskip("stardist")
pytest.importorskip("tensorflow")

from mbsi.segmentation.stardist_pipeline import expand_nuclei_to_cells, run_stardist_nuclei_segmentation


def _synthetic_nuclei_image(size: int = 128) -> np.ndarray:
    rng = np.random.default_rng(11)
    image = rng.integers(30, 60, (size, size), dtype=np.uint8)
    for cx, cy in [(30, 30), (80, 40), (50, 90)]:
        ys, xs = np.ogrid[:size, :size]
        mask = (xs - cx) ** 2 + (ys - cy) ** 2 <= 8 ** 2
        image[mask] = 220
    return image


def test_expand_nuclei_to_cells():
    nuclear = np.zeros((64, 64), dtype=np.int32)
    nuclear[20:30, 20:30] = 1
    nuclear[40:48, 40:48] = 2
    expanded = expand_nuclei_to_cells(nuclear, expansion_pixels=5)
    assert expanded.shape == nuclear.shape
    assert expanded.max() >= 2
    assert int(np.sum(expanded == 1)) > int(np.sum(nuclear == 1))


def test_run_stardist_nuclei_segmentation():
    image = _synthetic_nuclei_image()
    labels = run_stardist_nuclei_segmentation(image, n_tiles=(1, 1), channel="grayscale")
    assert labels.shape == image.shape
    assert labels.dtype == np.int32
    assert labels.max() > 0

    cell_mask = expand_nuclei_to_cells(labels, expansion_pixels=4)
    assert cell_mask.max() > 0
    assert int(np.sum(cell_mask > 0)) >= int(np.sum(labels > 0))
