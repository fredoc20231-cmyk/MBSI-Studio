"""
Diffusion kernel construction for MBSI.

Implements anisotropic Gaussian kernel using local diffusion tensors
derived from tissue morphology.
"""

from typing import Optional

import numpy as np


def build_diffusion_kernel(
    cell_coords: np.ndarray,
    spot_coords: np.ndarray,
    tensor_field: Optional[np.ndarray] = None,
    gamma: float = 1.0,
    sigma: Optional[float] = None,
    radius: Optional[float] = None,
    normalize: bool = True
) -> np.ndarray:
    """
    Build MBSI forward diffusion kernel from spots to cells.
    
    The kernel is defined as:
    K_{si} = exp[-d_D(x_s, x_i)^2 / (2 * sigma^2)]
    
    where d_D is the Mahalanobis distance using the local diffusion tensor.
    
    Parameters
    ----------
    cell_coords : ndarray
        Cell coordinates (n_cells x 2)
    spot_coords : ndarray
        Spot coordinates (n_spots x 2)
    tensor_field : ndarray, optional
        Diffusion tensor field (n_spots x 2 x 2). If None, uses isotropic.
    gamma : float
        Kernel scale parameter
    sigma : float, optional
        Bandwidth parameter. If None, estimated from data.
    radius : float, optional
        Maximum distance for kernel support. If None, no cutoff.
    normalize : bool
        If True, normalize kernel rows to sum to 1
        
    Returns
    -------
    kernel : ndarray
        Diffusion kernel (n_spots x n_cells)
    """
    n_spots = spot_coords.shape[0]
    n_cells = cell_coords.shape[0]
    
    # Default to isotropic diffusion
    if tensor_field is None:
        tensor_field = np.tile(np.eye(2)[np.newaxis, :, :], (n_spots, 1, 1))
    
    # Estimate sigma if not provided
    if sigma is None:
        # Use median pairwise distance as baseline
        from scipy.spatial.distance import pdist, squareform
        all_coords = np.vstack([spot_coords, cell_coords])
        dists = pdist(all_coords)
        sigma = np.median(dists) * gamma
    
    # Build kernel
    kernel = np.zeros((n_spots, n_cells))
    
    for s in range(n_spots):
        spot_pos = spot_coords[s]
        tensor = tensor_field[s]
        
        for c in range(n_cells):
            cell_pos = cell_coords[c]
            
            # Compute Mahalanobis distance
            diff = spot_pos - cell_pos
            inv_tensor = np.linalg.inv(tensor)
            mahalanobis_dist = np.sqrt(diff @ inv_tensor @ diff)
            
            # Apply radius cutoff if specified
            if radius is not None and mahalanobis_dist > radius:
                kernel[s, c] = 0.0
            else:
                # Gaussian kernel
                kernel[s, c] = np.exp(-(mahalanobis_dist**2) / (2 * sigma**2))
    
    # Normalize rows
    if normalize:
        row_sums = kernel.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0  # Avoid division by zero
        kernel = kernel / row_sums
    
    return kernel


def build_euclidean_kernel(
    coords1: np.ndarray,
    coords2: np.ndarray,
    sigma: Optional[float] = None,
    normalize: bool = True
) -> np.ndarray:
    """
    Build isotropic Euclidean Gaussian kernel (baseline).
    
    Parameters
    ----------
    coords1 : ndarray
        First set of coordinates (n1 x 2)
    coords2 : ndarray
        Second set of coordinates (n2 x 2)
    sigma : float, optional
        Bandwidth parameter
    normalize : bool
        If True, normalize rows
        
    Returns
    -------
    kernel : ndarray
        Kernel matrix (n1 x n2)
    """
    from scipy.spatial.distance import cdist
    
    # Compute pairwise distances
    dists = cdist(coords1, coords2, metric='euclidean')
    
    # Estimate sigma if not provided
    if sigma is None:
        sigma = np.median(dists)
    
    # Gaussian kernel
    kernel = np.exp(-(dists**2) / (2 * sigma**2))
    
    # Normalize rows
    if normalize:
        row_sums = kernel.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        kernel = kernel / row_sums
    
    return kernel


def compute_adaptive_bandwidth(
    coords: np.ndarray,
    k: int = 5
) -> np.ndarray:
    """
    Compute adaptive bandwidth for each point based on k-nearest neighbors.
    
    Parameters
    ----------
    coords : ndarray
        Coordinates (n x 2)
    k : int
        Number of nearest neighbors
        
    Returns
    -------
    bandwidths : ndarray
        Adaptive bandwidth for each point (n,)
    """
    from scipy.spatial.distance import pdist, squareform
    from scipy.spatial import KDTree
    
    tree = KDTree(coords)
    dists, _ = tree.query(coords, k=k+1)  # +1 to include self
    
    # Use distance to k-th neighbor as bandwidth
    bandwidths = dists[:, -1]
    
    return bandwidths
