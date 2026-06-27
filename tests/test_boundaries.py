"""Tests for boundaries module."""

import anndata as ad
import numpy as np


def test_detect_boundaries():
    from mbsi.boundaries import detect_tissue_boundaries, compute_boundary_leakage
    adata = ad.AnnData(X=np.random.rand(25, 10))
    adata.obsm["spatial"] = np.random.randn(25, 2)
    adata.obs["compartment"] = ["tumor"] * 12 + ["stroma"] * 13
    b = detect_tissue_boundaries(adata)
    assert "boundary_score" in b
    leak = compute_boundary_leakage(adata, boundaries=b)
    assert isinstance(leak, float)
