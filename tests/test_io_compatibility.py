"""Tests for module compatibility matrix."""

import anndata as ad
import numpy as np

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform


def _make_adata(n_obs=50, n_vars=100, with_cell_type=False):
    X = np.random.poisson(5, (n_obs, n_vars)).astype(float)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"g{i}" for i in range(n_vars)]
    adata.obs_names = [f"s{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = np.column_stack([np.random.rand(n_obs), np.random.rand(n_obs)])
    adata.obs["total_counts"] = X.sum(axis=1)
    if with_cell_type:
        adata.obs["cell_type"] = np.random.choice(["A", "B", "C"], n_obs)
    adata.uns["mbsi_platform"] = "visium"
    return adata


def test_compatibility_none():
    matrix = get_compatibility_matrix(None)
    assert matrix["qc"]["status"] == "unavailable"
    assert matrix["upload"]["status"] == "available"
    assert matrix["discovery"]["status"] == "unavailable"
    assert "recommended_next_step" in matrix["discovery"] or matrix["discovery"].get("reason")


def test_compatibility_visium_ready():
    adata = _make_adata()
    detection = detect_platform(["filtered_feature_bc_matrix.h5", "spatial/tissue_positions_list.csv"])
    matrix = get_compatibility_matrix(adata, detection)
    assert matrix["qc"]["status"] == "available"
    assert matrix["spatial_analysis"]["status"] == "available"
    assert matrix["benchmark_hub"]["status"] == "unavailable"
    assert "ground truth" in matrix["benchmark_hub"]["reason"].lower()


def test_compatibility_warn_low_genes():
    adata = _make_adata(n_obs=15, n_vars=10)
    matrix = get_compatibility_matrix(adata)
    assert matrix["spatial_analysis"]["status"] == "warn"
