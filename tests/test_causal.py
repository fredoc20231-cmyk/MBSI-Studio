"""Tests for causal module."""

import anndata as ad
import numpy as np


def test_causal_dag():
    from mbsi.causal import build_spatial_causal_dag, run_spatial_intervention
    adata = ad.AnnData(X=np.random.rand(20, 10))
    adata.var_names = [f"gene_{i}" for i in range(10)]
    adata.obsm["spatial"] = np.random.randn(20, 2)
    adata.obs["compartment"] = ["tumor"] * 10 + ["stroma"] * 10
    dag = build_spatial_causal_dag(adata)
    assert dag.number_of_nodes() > 0
    result = run_spatial_intervention(dag, "compartment", 0.0)
    assert "effects" in result
