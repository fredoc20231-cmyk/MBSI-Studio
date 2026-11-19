"""Tests for mbsi.morphology.segmentation module (19% -> target ~85%)."""

import numpy as np
import pytest

from mbsi.morphology.segmentation import (
    get_cell_centroids,
    overlay_segmentation,
    refine_segmentation,
    segment_cells,
)


def _make_image(H=64, W=64, seed=0):
    rng = np.random.RandomState(seed)
    img = rng.randint(0, 256, (H, W, 3)).astype(np.uint8)
    return img


def _make_labels(H=32, W=32):
    labels = np.zeros((H, W), dtype=np.int32)
    labels[4:12, 4:12] = 1
    labels[15:25, 15:25] = 2
    labels[5:10, 20:28] = 3
    return labels


def test_segment_cells_watershed():
    img = _make_image()
    labels = segment_cells(img, method="watershed")
    assert labels.shape == img.shape[:2]
    assert labels.dtype == np.int64 or np.issubdtype(labels.dtype, np.integer)


def test_segment_cells_threshold():
    img = _make_image()
    labels = segment_cells(img, method="threshold", min_size=10)
    assert labels.shape == img.shape[:2]


def test_segment_cells_grayscale():
    rng = np.random.RandomState(1)
    img = rng.randint(0, 256, (64, 64)).astype(np.uint8)
    labels = segment_cells(img, method="watershed")
    assert labels.shape == img.shape


def test_segment_cells_unknown_method():
    img = _make_image()
    with pytest.raises(ValueError, match="Unknown segmentation method"):
        segment_cells(img, method="invalid_method")


def test_get_cell_centroids():
    labels = _make_labels()
    centroids = get_cell_centroids(labels)
    assert centroids.ndim == 2
    assert centroids.shape[1] == 2
    assert centroids.shape[0] == 3


def test_overlay_segmentation_rgb():
    img = _make_image(32, 32)
    labels = _make_labels(32, 32)
    overlay = overlay_segmentation(img, labels)
    assert overlay.shape[:2] == img.shape[:2]


def test_overlay_segmentation_grayscale():
    img = np.random.RandomState(0).randint(0, 256, (32, 32)).astype(np.uint8)
    labels = _make_labels(32, 32)
    overlay = overlay_segmentation(img, labels)
    assert overlay.shape[:2] == (32, 32)


def test_refine_segmentation_removes_small():
    labels = np.zeros((32, 32), dtype=np.int32)
    labels[2:4, 2:4] = 1  # 4 pixels - small
    labels[10:25, 10:25] = 2  # 225 pixels - large
    refined = refine_segmentation(labels, min_size=10)
    assert 1 not in refined or (refined == 1).sum() == 0


def test_refine_segmentation_max_size():
    labels = np.zeros((32, 32), dtype=np.int32)
    labels[2:4, 2:4] = 1
    labels[10:25, 10:25] = 2
    refined = refine_segmentation(labels, min_size=2, max_size=300)
    assert isinstance(refined, np.ndarray)
