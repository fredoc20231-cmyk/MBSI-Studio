"""Tests for communication module."""

import anndata as ad
import numpy as np


def test_signaling_graph():
    from mbsi.communication import compute_ligand_diffusion_field, build_spatial_signaling_graph
    genes = ["TGFB1", "TGFBR1", "GENE2"]
    adata = ad.AnnData(X=np.random.rand(20, 3))
    adata.var_names = genes
    adata.obsm["spatial"] = np.random.randn(20, 2)
    field = compute_ligand_diffusion_field(adata, ["TGFB1"])
    assert field.shape[0] == 20
    graph = build_spatial_signaling_graph(adata, [("TGFB1", "TGFBR1")])
    assert "flux_table" in graph
