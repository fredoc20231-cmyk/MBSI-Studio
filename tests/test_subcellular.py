"""Tests for subcellular module."""

import anndata as ad
import numpy as np


def test_infer_subcellular():
    from mbsi.subcellular import infer_subcellular_compartments, partition_transcripts_by_compartment
    adata = ad.AnnData(X=np.random.rand(20, 15))
    adata.obsm["spatial"] = np.random.randn(20, 2)
    sub = infer_subcellular_compartments(adata)
    assert "nuclear_score" in sub
    out = partition_transcripts_by_compartment(adata, sub)
    assert "nuclear_expr" in out.obs
