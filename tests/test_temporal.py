"""Tests for temporal module."""

import anndata as ad
import numpy as np


def test_temporal_simulation():
    from mbsi.temporal import align_spatial_timepoints, simulate_tissue_future
    a1 = ad.AnnData(X=np.random.rand(10, 5))
    a1.obsm["spatial"] = np.random.randn(10, 2)
    a2 = ad.AnnData(X=np.random.rand(10, 5))
    a2.obsm["spatial"] = np.random.randn(10, 2)
    align = align_spatial_timepoints([a1, a2])
    assert len(align["alignments"]) == 2
    sim = simulate_tissue_future({"compartments": {"tumor": 0.4, "immune": 0.2}}, steps=3)
    assert len(sim["trajectory"]) == 4
