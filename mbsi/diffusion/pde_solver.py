"""
PDE solver for diffusion equations.

Provides numerical solvers for diffusion PDEs with spatially varying
coefficients, which can be used for more accurate modeling.
"""

from typing import Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix, linalg


def solve_diffusion_pde(
    initial_condition: np.ndarray,
    tensor_field: np.ndarray,
    dt: float = 0.01,
    n_steps: int = 100,
    boundary_condition: str = "neumann"
) -> np.ndarray:
    """
    Solve time-dependent diffusion equation: du/dt = div(D(x) * grad u)
    
    Parameters
    ----------
    initial_condition : ndarray
        Initial condition (H x W)
    tensor_field : ndarray
        Diffusion tensor field (H x W x 2 x 2)
    dt : float
        Time step
    n_steps : int
        Number of time steps
    boundary_condition : str
        Boundary condition: 'neumann' or 'dirichlet'
        
    Returns
    -------
    solution : ndarray
        Solution at final time (H x W)
    """
    H, W = initial_condition.shape
    u = initial_condition.copy()
    
    # Build Laplacian matrix
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    
    # Time stepping using implicit Euler
    I = csr_matrix(np.eye(H * W))
    
    for _ in range(n_steps):
        # Solve: (I - dt * L) * u_new = u_old
        u_flat = u.flatten()
        u_new_flat = linalg.spsolve(I - dt * L, u_flat)
        u = u_new_flat.reshape(H, W)
    
    return u


def solve_steady_state(
    source: np.ndarray,
    tensor_field: np.ndarray,
    grid_size: Tuple[int, int],
    epsilon: float = 1e-6
) -> np.ndarray:
    """
    Solve steady-state diffusion equation: -div(D(x) * grad u) = source
    
    Parameters
    ----------
    source : ndarray
        Source term (H x W)
    tensor_field : ndarray
        Diffusion tensor field (H x W x 2 x 2)
    grid_size : tuple
        Grid size (H, W)
    epsilon : float
        Regularization parameter
        
    Returns
    -------
    solution : ndarray
        Steady-state solution (H x W)
    """
    from mbsi.diffusion.green_function import build_variable_diffusion_laplacian
    
    H, W = grid_size
    n_points = H * W
    
    # Build Laplacian
    L = build_variable_diffusion_laplacian(tensor_field, grid_size)
    
    # Solve linear system
    source_flat = source.flatten()
    solution_flat = linalg.spsolve(L + epsilon * csr_matrix(np.eye(n_points)), 
                                  source_flat)
    
    return solution_flat.reshape(H, W)


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
                    direction = np.array([dj, di])
                    weight = direction @ tensor @ direction
                    
                    data.append(weight)
                    row_indices.append(idx)
                    col_indices.append(nidx)
    
    laplacian = csr_matrix((data, (row_indices, col_indices)), 
                          shape=(n_points, n_points))
    
    return laplacian
