"""Tests for MBSI solver sparse input and spatial validation."""

import anndata as ad
import numpy as np
import pytest
from scipy.sparse import csr_matrix

from mbsi.reconstruction.solver import run_mbsi

pytestmark = pytest.mark.heavy


def _spot_adata(n_spots=8, n_genes=20, sparse=False):
    if sparse:
        X = csr_matrix(np.random.poisson(3, (n_spots, n_genes)).astype(float))
    else:
        X = np.random.rand(n_spots, n_genes)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    adata.obs_names = [f"spot_{i}" for i in range(n_spots)]
    adata.obsm["spatial"] = np.random.randn(n_spots, 2)
    return adata


def test_run_mbsi_csr_input():
    adata = _spot_adata(sparse=True)
    recon = run_mbsi(adata, n_cells_per_spot=3, max_iter=30, random_state=0)
    assert recon.n_obs == adata.n_obs * 3
    assert recon.n_vars == adata.n_vars
    assert np.isfinite(recon.X).all()


def test_run_mbsi_missing_spatial_raises():
    adata = _spot_adata()
    del adata.obsm["spatial"]
    with pytest.raises(ValueError, match="obsm\\['spatial'\\]"):
        run_mbsi(adata, max_iter=10, random_state=0)
