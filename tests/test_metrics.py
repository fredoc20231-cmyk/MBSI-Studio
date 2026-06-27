"""
Tests for benchmark metrics module.
"""

import pytest
import numpy as np
import anndata as ad


def test_compute_correlation():
    """Test correlation computation."""
    from mbsi.benchmarks.metrics import compute_correlation
    
    n = 100
    x = np.random.randn(n)
    y = x + 0.1 * np.random.randn(n)  # Correlated
    
    corr = compute_correlation(x.reshape(-1, 1), y.reshape(-1, 1), method='pearson')
    
    # Should be high correlation
    assert corr > 0.8
    assert isinstance(corr, float)


def test_compute_rmse():
    """Test RMSE computation."""
    from mbsi.benchmarks.metrics import compute_rmse
    
    n = 100
    x = np.random.randn(n)
    y = x + 0.1 * np.random.randn(n)
    
    rmse = compute_rmse(x.reshape(-1, 1), y.reshape(-1, 1))
    
    assert rmse >= 0
    assert isinstance(rmse, float)


def test_compute_all_metrics():
    """Test comprehensive metrics computation."""
    from mbsi.benchmarks.metrics import compute_all_metrics
    
    n_cells = 50
    n_genes = 20
    
    # Create true and reconstructed data
    X_true = np.random.rand(n_cells, n_genes)
    X_recon = X_true + 0.1 * np.random.randn(n_cells, n_genes)
    
    coords = np.random.randn(n_cells, 2)
    
    true_adata = ad.AnnData(X=X_true)
    true_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    true_adata.obsm['spatial'] = coords
    
    recon_adata = ad.AnnData(X=X_recon)
    recon_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    recon_adata.obsm['spatial'] = coords
    
    metrics = compute_all_metrics(true_adata, recon_adata)
    
    # Check metrics exist
    assert 'pearson_correlation' in metrics
    assert 'rmse' in metrics
    assert 'r2_score' in metrics


def test_align_reconstruction_to_truth():
    """Test spatial alignment when cell counts differ."""
    from mbsi.benchmarks.metrics import align_reconstruction_to_truth

    n_true = 20
    n_recon = 60
    n_genes = 10
    genes = [f"gene_{i}" for i in range(n_genes)]

    true_adata = ad.AnnData(X=np.random.rand(n_true, n_genes))
    true_adata.var_names = genes
    true_adata.obsm['spatial'] = np.random.randn(n_true, 2)

    recon_adata = ad.AnnData(X=np.random.rand(n_recon, n_genes))
    recon_adata.var_names = genes
    recon_adata.obsm['spatial'] = np.random.randn(n_recon, 2)

    true_expr, aligned_recon = align_reconstruction_to_truth(true_adata, recon_adata, genes)
    assert true_expr.shape == (n_true, n_genes)
    assert aligned_recon.shape == (n_true, n_genes)


def test_spatial_metrics_with_mismatched_counts():
    """Spatial metrics should be computed when cell counts differ."""
    from mbsi.benchmarks.metrics import compute_all_metrics

    n_true = 15
    n_recon = 45
    n_genes = 8
    genes = [f"gene_{i}" for i in range(n_genes)]

    true_adata = ad.AnnData(X=np.random.rand(n_true, n_genes))
    true_adata.var_names = genes
    true_adata.obs_names = [f"cell_{i}" for i in range(n_true)]
    true_adata.obsm['spatial'] = np.random.randn(n_true, 2)

    recon_adata = ad.AnnData(X=np.random.rand(n_recon, n_genes))
    recon_adata.var_names = genes
    recon_adata.obs_names = [f"recon_{i}" for i in range(n_recon)]
    recon_adata.obsm['spatial'] = np.random.randn(n_recon, 2)

    metrics = compute_all_metrics(true_adata, recon_adata)
    assert metrics['spatial_correlation'] is not None
    assert metrics['marker_localization'] is not None
    assert metrics['morans_i_true'] is not None
    assert metrics['morans_i_recon'] is not None

    """Test pseudo-Visium generation."""
    from mbsi.benchmarks.pseudo_visium import make_pseudo_visium
    
    n_cells = 100
    n_genes = 50
    
    X = np.random.rand(n_cells, n_genes)
    coords = np.random.randn(n_cells, 2)
    
    single_cell_adata = ad.AnnData(X=X)
    single_cell_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    single_cell_adata.obsm['spatial'] = coords
    
    pseudo_visium = make_pseudo_visium(
        single_cell_adata,
        spot_diameter=55.0,
        aggregation="hex",
        n_spots=20,
        random_state=42
    )
    
    assert pseudo_visium.n_obs <= 20
    assert pseudo_visium.n_vars == n_genes
    assert 'spatial' in pseudo_visium.obsm
