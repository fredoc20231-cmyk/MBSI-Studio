"""
Competitor/baseline methods for comparison.

Implements simple baseline methods for spatial transcriptomics
deconvolution to compare against MBSI.
"""

from typing import Optional

import anndata as ad
import numpy as np
from scipy.spatial.distance import cdist


def run_baseline_methods(
    spot_adata: ad.AnnData,
    cell_coords: Optional[np.ndarray] = None,
    n_cells_per_spot: int = 5,
    random_state: Optional[int] = None
) -> dict:
    """
    Run various baseline methods for comparison.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level data
    cell_coords : ndarray, optional
        Cell coordinates
    n_cells_per_spot : int
        Cells per spot for pseudo-cell generation
    random_state : int, optional
        Random seed
        
    Returns
    -------
    results : dict
        Dictionary with baseline reconstructions
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    results = {}
    
    # Generate cell coordinates if not provided
    if cell_coords is None:
        from mbsi.reconstruction.solver import generate_pseudo_cells
        cell_coords = generate_pseudo_cells(
            spot_adata.obsm['spatial'],
            n_cells_per_spot=n_cells_per_spot,
            random_state=random_state
        )
    
    # Method 1: Uniform distribution
    results['uniform'] = baseline_uniform(spot_adata, cell_coords, n_cells_per_spot)
    
    # Method 2: Distance-weighted
    results['distance_weighted'] = baseline_distance_weighted(
        spot_adata, cell_coords, n_cells_per_spot
    )
    
    # Method 3: Nearest neighbor
    results['nearest_neighbor'] = baseline_nearest_neighbor(
        spot_adata, cell_coords
    )
    
    # Method 4: Linear interpolation
    results['linear_interp'] = baseline_linear_interpolation(
        spot_adata, cell_coords
    )
    
    return results


def baseline_uniform(
    spot_adata: ad.AnnData,
    cell_coords: np.ndarray,
    n_cells_per_spot: int
) -> ad.AnnData:
    """
    Uniform distribution baseline.
    
    Distributes spot expression uniformly to cells within each spot.
    """
    n_cells = len(cell_coords)
    n_spots = spot_adata.n_obs
    n_genes = spot_adata.n_vars
    
    # Initialize cell expression
    cell_expression = np.zeros((n_cells, n_genes))
    
    # Distribute uniformly
    for i in range(n_spots):
        start_idx = i * n_cells_per_spot
        end_idx = min((i + 1) * n_cells_per_spot, n_cells)
        
        spot_expr = spot_adata.X[i]
        if hasattr(spot_expr, 'toarray'):
            spot_expr = spot_expr.toarray().flatten()
        
        # Uniform distribution
        cell_expression[start_idx:end_idx] = spot_expr / n_cells_per_spot
    
    # Create AnnData
    baseline_adata = ad.AnnData(X=cell_expression, dtype=np.float32)
    baseline_adata.var_names = spot_adata.var_names.copy()
    baseline_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    baseline_adata.obsm['spatial'] = cell_coords
    
    return baseline_adata


def baseline_distance_weighted(
    spot_adata: ad.AnnData,
    cell_coords: np.ndarray,
    n_cells_per_spot: int
) -> ad.AnnData:
    """
    Distance-weighted baseline.
    
    Distributes spot expression to cells weighted by distance.
    """
    spot_coords = spot_adata.obsm['spatial']
    n_cells = len(cell_coords)
    n_spots = spot_adata.n_obs
    n_genes = spot_adata.n_vars
    
    # Compute distance matrix
    dists = cdist(spot_coords, cell_coords)
    
    # Initialize cell expression
    cell_expression = np.zeros((n_cells, n_genes))
    
    # Distribute based on distance
    for i in range(n_spots):
        spot_expr = spot_adata.X[i]
        if hasattr(spot_expr, 'toarray'):
            spot_expr = spot_expr.toarray().flatten()
        
        # Get cells for this spot
        start_idx = i * n_cells_per_spot
        end_idx = min((i + 1) * n_cells_per_spot, n_cells)
        
        cell_dists = dists[i, start_idx:end_idx]
        
        # Weight by inverse distance
        weights = 1.0 / (cell_dists + 1e-10)
        weights = weights / weights.sum()
        
        # Distribute
        for j, idx in enumerate(range(start_idx, end_idx)):
            cell_expression[idx] = weights[j] * spot_expr
    
    # Create AnnData
    baseline_adata = ad.AnnData(X=cell_expression, dtype=np.float32)
    baseline_adata.var_names = spot_adata.var_names.copy()
    baseline_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    baseline_adata.obsm['spatial'] = cell_coords
    
    return baseline_adata


def baseline_nearest_neighbor(
    spot_adata: ad.AnnData,
    cell_coords: np.ndarray
) -> ad.AnnData:
    """
    Nearest neighbor baseline.
    
    Each cell gets expression from nearest spot.
    """
    spot_coords = spot_adata.obsm['spatial']
    n_cells = len(cell_coords)
    n_genes = spot_adata.n_vars
    
    # Find nearest spot for each cell
    from scipy.spatial import KDTree
    tree = KDTree(spot_coords)
    _, indices = tree.query(cell_coords, k=1)
    
    # Initialize cell expression
    cell_expression = np.zeros((n_cells, n_genes))
    
    # Assign nearest spot expression
    for i in range(n_cells):
        spot_idx = indices[i]
        spot_expr = spot_adata.X[spot_idx]
        if hasattr(spot_expr, 'toarray'):
            spot_expr = spot_expr.toarray().flatten()
        
        cell_expression[i] = spot_expr
    
    # Create AnnData
    baseline_adata = ad.AnnData(X=cell_expression, dtype=np.float32)
    baseline_adata.var_names = spot_adata.var_names.copy()
    baseline_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    baseline_adata.obsm['spatial'] = cell_coords
    
    return baseline_adata


def baseline_linear_interpolation(
    spot_adata: ad.AnnData,
    cell_coords: np.ndarray
) -> ad.AnnData:
    """
    Linear interpolation baseline.
    
    Interpolates expression from neighboring spots.
    """
    spot_coords = spot_adata.obsm['spatial']
    n_cells = len(cell_coords)
    n_genes = spot_adata.n_vars
    
    # Use 3 nearest spots for interpolation
    from scipy.spatial import KDTree
    tree = KDTree(spot_coords)
    dists, indices = tree.query(cell_coords, k=min(3, len(spot_coords)))
    
    # Initialize cell expression
    cell_expression = np.zeros((n_cells, n_genes))
    
    # Interpolate
    for i in range(n_cells):
        neighbor_dists = dists[i]
        neighbor_indices = indices[i]
        
        # Weight by inverse distance
        weights = 1.0 / (neighbor_dists + 1e-10)
        weights = weights / weights.sum()
        
        # Interpolate expression
        cell_expr = np.zeros(n_genes)
        for j, spot_idx in enumerate(neighbor_indices):
            spot_expr = spot_adata.X[spot_idx]
            if hasattr(spot_expr, 'toarray'):
                spot_expr = spot_expr.toarray().flatten()
            
            cell_expr += weights[j] * spot_expr
        
        cell_expression[i] = cell_expr
    
    # Create AnnData
    baseline_adata = ad.AnnData(X=cell_expression, dtype=np.float32)
    baseline_adata.var_names = spot_adata.var_names.copy()
    baseline_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    baseline_adata.obsm['spatial'] = cell_coords
    
    return baseline_adata
