"""Tests for mbsi.io.validators module (58% -> target ~95%)."""

import anndata as ad
import numpy as np

from mbsi.io.validators import validate_spatial_adata


def _make_valid_adata(n_obs=20, n_vars=10, seed=0):
    rng = np.random.RandomState(seed)
    adata = ad.AnnData(X=rng.rand(n_obs, n_vars).astype(np.float32))
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"spot_{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = rng.rand(n_obs, 2).astype(np.float32)
    return adata


def test_valid_adata():
    adata = _make_valid_adata()
    result = validate_spatial_adata(adata)
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert result["has_spatial"] is True
    assert result["n_spots"] == 20
    assert result["n_genes"] == 10


def test_missing_spatial():
    adata = _make_valid_adata()
    del adata.obsm["spatial"]
    result = validate_spatial_adata(adata)
    assert result["valid"] is False
    assert result["has_spatial"] is False
    assert any("spatial" in e.lower() for e in result["errors"])


def test_wrong_spatial_dimensions():
    adata = _make_valid_adata()
    adata.obsm["spatial"] = np.random.rand(adata.n_obs, 3).astype(np.float32)
    result = validate_spatial_adata(adata)
    assert result["valid"] is False
    assert any("2D" in e for e in result["errors"])


def test_few_spots_warning():
    adata = _make_valid_adata(n_obs=5)
    result = validate_spatial_adata(adata)
    assert result["valid"] is True
    assert any("few spots" in w.lower() for w in result["warnings"])


def test_few_genes_warning():
    adata = _make_valid_adata(n_vars=5)
    result = validate_spatial_adata(adata)
    assert result["valid"] is True
    assert any("few genes" in w.lower() for w in result["warnings"])


def test_nan_values_warning():
    adata = _make_valid_adata()
    X = adata.X.copy()
    X[0, 0] = np.nan
    adata = ad.AnnData(X=X)
    adata.var_names = [f"gene_{i}" for i in range(X.shape[1])]
    adata.obs_names = [f"spot_{i}" for i in range(X.shape[0])]
    adata.obsm["spatial"] = np.random.rand(X.shape[0], 2).astype(np.float32)
    result = validate_spatial_adata(adata)
    assert any("NaN" in w for w in result["warnings"])


def test_inf_values_warning():
    adata = _make_valid_adata()
    X = adata.X.copy()
    X[0, 0] = np.inf
    adata = ad.AnnData(X=X)
    adata.var_names = [f"gene_{i}" for i in range(X.shape[1])]
    adata.obs_names = [f"spot_{i}" for i in range(X.shape[0])]
    adata.obsm["spatial"] = np.random.rand(X.shape[0], 2).astype(np.float32)
    result = validate_spatial_adata(adata)
    assert any("Inf" in w for w in result["warnings"])


def test_sufficient_data_no_warnings():
    adata = _make_valid_adata(n_obs=50, n_vars=50)
    result = validate_spatial_adata(adata)
    assert result["valid"] is True
    assert len(result["warnings"]) == 0
