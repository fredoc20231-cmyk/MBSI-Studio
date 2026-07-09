"""
Tests for reconstruction module.
"""

import pytest
import numpy as np
import anndata as ad

pytestmark = pytest.mark.heavy


def test_run_mbsi():
    """Test MBSI reconstruction."""
    from mbsi.reconstruction.solver import run_mbsi
    
    # Create test spot data
    n_spots = 10
    n_genes = 20
    X = np.random.rand(n_spots, n_genes)
    spot_adata = ad.AnnData(X=X)
    spot_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    spot_adata.obs_names = [f"spot_{i}" for i in range(n_spots)]
    spot_adata.obsm['spatial'] = np.random.randn(n_spots, 2)
    
    # Run reconstruction
    reconstructed = run_mbsi(
        spot_adata,
        n_cells_per_spot=5,
        gamma=1.0,
        epsilon=0.05,
        lambda_sheaf=0.1,
        max_iter=50,
        random_state=42
    )
    
    # Check output
    assert reconstructed.n_obs == n_spots * 5
    assert reconstructed.n_vars == n_genes
    assert 'spatial' in reconstructed.obsm
    assert reconstructed.obsm['spatial'].shape == (n_spots * 5, 2)
    assert 'parameters' in reconstructed.uns
    assert 'convergence' in reconstructed.uns


def test_reconstruction_output_dimensions():
    """Test reconstruction output dimensions."""
    from mbsi.reconstruction.solver import run_mbsi
    
    n_spots = 5
    n_genes = 10
    n_cells_per_spot = 3
    
    X = np.random.rand(n_spots, n_genes)
    spot_adata = ad.AnnData(X=X)
    spot_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    spot_adata.obs_names = [f"spot_{i}" for i in range(n_spots)]
    spot_adata.obsm['spatial'] = np.random.randn(n_spots, 2)
    
    reconstructed = run_mbsi(
        spot_adata,
        n_cells_per_spot=n_cells_per_spot,
        max_iter=20,
        random_state=42
    )
    
    assert reconstructed.n_obs == n_spots * n_cells_per_spot
    assert reconstructed.n_vars == n_genes
    assert reconstructed.X.shape == (n_spots * n_cells_per_spot, n_genes)


def test_run_iterative_mbsi():
    """Test iterative MBSI reconstruction."""
    from mbsi.reconstruction.solver import run_iterative_mbsi

    n_spots = 10
    n_genes = 20
    X = np.random.rand(n_spots, n_genes)
    spot_adata = ad.AnnData(X=X)
    spot_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    spot_adata.obs_names = [f"spot_{i}" for i in range(n_spots)]
    spot_adata.obsm['spatial'] = np.random.randn(n_spots, 2)

    reconstructed = run_iterative_mbsi(
        spot_adata,
        n_cells_per_spot=3,
        max_outer_iter=2,
        max_inner_iter=20,
        random_state=42
    )

    assert reconstructed.n_obs == n_spots * 3
    assert reconstructed.uns['parameters']['iterative'] is True


def test_apply_sheaf_regularization():
    """Test sheaf Laplacian regularization."""
    from mbsi.reconstruction.solver import apply_sheaf_regularization
    from mbsi.sheaf.graph_builder import build_cell_graph

    n_cells = 12
    n_genes = 5
    coords = np.random.randn(n_cells, 2)
    graph = build_cell_graph(coords, k=3)
    expression = np.random.rand(n_cells, n_genes)

    smoothed = apply_sheaf_regularization(expression, graph, lambda_sheaf=0.2, max_iter=10)
    assert smoothed.shape == expression.shape
    assert not np.allclose(smoothed, expression)

    """Test pseudo-cell generation."""
    from mbsi.reconstruction.solver import generate_pseudo_cells
    
    n_spots = 10
    spot_coords = np.random.randn(n_spots, 2)
    n_cells_per_spot = 5
    
    cell_coords = generate_pseudo_cells(
        spot_coords,
        n_cells_per_spot=n_cells_per_spot,
        random_state=42
    )
    
    assert cell_coords.shape == (n_spots * n_cells_per_spot, 2)
    assert cell_coords.shape[0] == n_spots * n_cells_per_spot
