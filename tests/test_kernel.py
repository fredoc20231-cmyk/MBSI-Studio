"""
Tests for diffusion kernel module.
"""

import pytest
import numpy as np


def test_build_diffusion_kernel():
    """Test diffusion kernel construction."""
    from mbsi.diffusion.kernel import build_diffusion_kernel
    
    # Create test coordinates
    n_cells = 20
    n_spots = 10
    cell_coords = np.random.randn(n_cells, 2)
    spot_coords = np.random.randn(n_spots, 2)
    
    # Build kernel
    kernel = build_diffusion_kernel(cell_coords, spot_coords, gamma=1.0)
    
    # Check shape
    assert kernel.shape == (n_spots, n_cells)
    
    # Check normalization (rows sum to 1)
    row_sums = kernel.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-6)
    
    # Check non-negativity
    assert np.all(kernel >= 0)


def test_build_euclidean_kernel():
    """Test Euclidean kernel construction."""
    from mbsi.diffusion.kernel import build_euclidean_kernel
    
    coords1 = np.random.randn(10, 2)
    coords2 = np.random.randn(15, 2)
    
    kernel = build_euclidean_kernel(coords1, coords2, sigma=1.0)
    
    assert kernel.shape == (10, 15)
    assert np.all(kernel >= 0)
    
    # Check normalization
    row_sums = kernel.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-6)


def test_kernel_symmetry():
    """Test kernel symmetry properties."""
    from mbsi.diffusion.kernel import build_euclidean_kernel
    
    coords = np.random.randn(10, 2)
    
    kernel = build_euclidean_kernel(coords, coords, sigma=1.0, normalize=False)
    
    # Should be symmetric for same coordinates
    assert np.allclose(kernel, kernel.T, atol=1e-6)
