"""Tests for segmentation module."""

import numpy as np
import anndata as ad


def test_segment_tissue_coords():
    from mbsi.segmentation import segment_tissue
    coords = np.random.randn(30, 2)
    mask = segment_tissue(coords=coords)
    assert len(mask) == 30


def test_voronoi_regions():
    from mbsi.segmentation.masks import voronoi_cell_regions
    coords = np.random.randn(20, 2)
    regions = voronoi_cell_regions(coords)
    assert len(regions) == 20


def test_assign_compartments():
    from mbsi.segmentation import assign_spots_to_compartments
    adata = ad.AnnData(X=np.random.rand(15, 10))
    adata.obsm["spatial"] = np.random.randn(15, 2)
    out = assign_spots_to_compartments(adata)
    assert "compartment" in out.obs
