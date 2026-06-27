"""Tests for multimodal module."""

import anndata as ad
import numpy as np


def test_multimodal_embedding():
    from mbsi.multimodal import build_multimodal_embedding, fuse_rna_image_protein
    adata = ad.AnnData(X=np.random.rand(15, 10))
    fused = fuse_rna_image_protein(adata, protein=np.random.rand(15, 3))
    emb = build_multimodal_embedding(fused)
    assert emb.shape[0] == 15
