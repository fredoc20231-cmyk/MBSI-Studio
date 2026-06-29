"""Tests for Voronoi cell generation."""

import numpy as np

from mbsi.segmentation import generate_voronoi_cells
from mbsi.segmentation.masks import voronoi_cell_regions


def test_generate_voronoi_cells():
    coords = np.random.randn(25, 2)
    labels = generate_voronoi_cells(coords)
    assert len(labels) == 25
    assert labels.dtype == np.int32


def test_voronoi_with_clip_mask():
    coords = np.random.randn(20, 2)
    clip = np.ones(20, dtype=bool)
    clip[:5] = False
    labels = generate_voronoi_cells(coords, clip_mask=clip)
    assert (labels[:5] == -1).all()


def test_voronoi_cell_regions_alias():
    coords = np.random.randn(15, 2)
    regions = voronoi_cell_regions(coords)
    assert len(regions) == 15


def test_small_coord_set():
    coords = np.random.randn(3, 2)
    labels = generate_voronoi_cells(coords)
    assert len(labels) == 3
