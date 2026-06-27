"""
Tests for data loading module.
"""

import pytest
import numpy as np
import anndata as ad
from pathlib import Path
import tempfile


def test_load_h5ad():
    """Test loading h5ad file."""
    # Create temporary h5ad file
    with tempfile.NamedTemporaryFile(suffix='.h5ad', delete=False) as f:
        temp_path = f.name
    
    try:
        # Create test AnnData
        n_obs = 10
        n_vars = 20
        X = np.random.randn(n_obs, n_vars)
        adata = ad.AnnData(X=X)
        adata.var_names = [f"gene_{i}" for i in range(n_vars)]
        adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
        adata.obsm['spatial'] = np.random.randn(n_obs, 2)
        
        # Save and load
        adata.write_h5ad(temp_path)
        
        from mbsi.io.loaders import load_h5ad
        loaded = load_h5ad(temp_path)
        
        assert loaded.n_obs == n_obs
        assert loaded.n_vars == n_vars
        assert 'spatial' in loaded.obsm
        assert loaded.obsm['spatial'].shape == (n_obs, 2)
        
    finally:
        Path(temp_path).unlink()


def test_validate_spatial_adata():
    """Test spatial AnnData validation."""
    from mbsi.io.validators import validate_spatial_adata
    
    # Valid AnnData
    n_obs = 10
    n_vars = 20
    X = np.random.randn(n_obs, n_vars)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    adata.obsm['spatial'] = np.random.randn(n_obs, 2)
    
    validation = validate_spatial_adata(adata)
    
    assert validation['valid'] == True
    assert validation['has_spatial'] == True
    assert validation['n_spots'] == n_obs
    assert validation['n_genes'] == n_vars
    
    # Invalid AnnData (no spatial coordinates)
    adata_no_spatial = ad.AnnData(X=X)
    validation = validate_spatial_adata(adata_no_spatial)
    
    assert validation['valid'] == False
    assert validation['has_spatial'] == False
    assert len(validation['errors']) > 0
