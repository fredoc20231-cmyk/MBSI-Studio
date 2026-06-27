"""
Green's function computation for diffusion PDE.

Provides functions for computing Green's functions of the diffusion operator,
which can be used for more accurate kernel construction.
"""

from typing import Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix, linalg


def compute_green_function(
    tensor_field: np.ndarray,
    source: np.ndarray,
    grid_size: Tuple[int, int],
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Compute Green's function for diffusion equation with spatially varying tensor.
    
    Solves: -div(D(x) * grad G) = delta(x - source)
    
    Parameters
    ----------
    tensor_field : ndarray
        Diffusion tensor field (H x W x 2 x 2)
    source : ndarray
        Source point coordinates (2,)
    grid_size : tuple
        Grid size (H, W)
    epsilon : float
        Regularization parameter
        
    Returns
    -------
    green : ndarray
        Green's function on grid (H x W)
    """
    H, W = grid_size
    n_points = H * W
    
    # Build Laplacian matrix with spatially varying diffusion
    L = build_variable_diffusion_laplacian(tensor_field, grid_size)
    
    # Build source vector
    source_idx = int(source[1] * W + source[0])
    b = np.zeros(n_points)
    b[source_idx] = 1.0
    
    # Solve linear system
    green_flat = linalg.spsolve(L + epsilon * csr_matrix(np.eye(n_points)), b)
    
    return green_flat.reshape(H, W)


def build_variable_diffusion_laplacian(
    tensor_field: np.ndarray,
    grid_size: Tuple[int, int]
) -> csr_matrix:
    """
    Build discretized Laplacian with spatially varying diffusion tensor.
    
    Parameters
    ----------
    tensor_field : ndarray
        Diffusion tensor field (H x W x 2 x 2)
    grid_size : tuple
        Grid size (H, W)
        
    Returns
    -------
    laplacian : csr_matrix
        Sparse Laplacian matrix (n_points x n_points)
    """
    H, W = grid_size
    n_points = H * W
    
    # Build using finite differences
    data = []
    row_indices = []
    col_indices = []
    
    for i in range(H):
        for j in range(W):
            idx = i * W + j
            tensor = tensor_field[i, j]
            
            # Center point
            data.append(-4.0)
            row_indices.append(idx)
            col_indices.append(idx)
            
            # Neighbors with tensor-weighted differences
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                
                if 0 <= ni < H and 0 <= nj < W:
                    nidx = ni * W + nj
                    
                    # Use tensor to weight the connection
                    direction = np.array([dj, di])  # Note: j is x, i is y
                    weight = direction @ tensor @ direction
                    
                    data.append(weight)
                    row_indices.append(idx)
                    col_indices.append(nidx)
    
    laplacian = csr_matrix((data, (row_indices, col_indices)), 
                          shape=(n_points, n_points))
    
    return laplacian


def compute_fundamental_solution(
    tensor: np.ndarray,
    distance: float
) -> float:
    """
    Compute fundamental solution (Green's function) for constant diffusion tensor.
    
    For 2D: G(x) = -1/(2*pi*sqrt(det(D))) * log(|x|)
    
    Parameters
    ----------
    tensor : ndarray
        Constant diffusion tensor (2 x 2)
    distance : float
        Distance from source
        
    Returns
    -------
    green : float
        Green's function value
    """
    det = np.linalg.det(tensor)
    
    if det <= 0:
        raise ValueError("Diffusion tensor must be positive definite")
    
    green = -1.0 / (2 * np.pi * np.sqrt(det)) * np.log(distance + 1e-10)
    
    return green
