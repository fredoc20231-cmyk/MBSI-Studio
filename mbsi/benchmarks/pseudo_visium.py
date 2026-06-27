"""
Pseudo-Visium generation for validation.

Creates spot-level aggregates from single-cell data to simulate
Visium-style spatial transcriptomics for benchmarking.
"""

from typing import Optional, Literal

import anndata as ad
import numpy as np
from scipy.spatial import KDTree


def make_pseudo_visium(
    single_cell_adata: ad.AnnData,
    spot_diameter: float = 55.0,
    aggregation: Literal["hex", "grid", "random"] = "hex",
    n_spots: Optional[int] = None,
    random_state: Optional[int] = None
) -> ad.AnnData:
    """
    Generate pseudo-Visium data from single-cell ground truth.
    
    Parameters
    ----------
    single_cell_adata : AnnData
        Single-cell AnnData with spatial coordinates in obsm['spatial']
    spot_diameter : float
        Diameter of Visium spots in microns
    aggregation : str
        Spot arrangement: 'hex' (hexagonal), 'grid', or 'random'
    n_spots : int, optional
        Number of spots to generate. If None, estimated from data.
    random_state : int, optional
        Random seed
        
    Returns
    -------
    pseudo_visium : AnnData
        Pseudo-Visium AnnData with:
        - X: aggregated expression (n_spots x n_genes)
        - obsm['spatial']: spot coordinates
        - uns['spot_diameter']: spot diameter
        - uns['aggregation']: aggregation method
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    cell_coords = single_cell_adata.obsm['spatial']
    cell_expression = single_cell_adata.X
    n_genes = single_cell_adata.n_vars
    
    # Estimate number of spots if not specified
    if n_spots is None:
        # Estimate based on spatial extent
        x_range = cell_coords[:, 0].max() - cell_coords[:, 0].min()
        y_range = cell_coords[:, 1].max() - cell_coords[:, 1].min()
        area = x_range * y_range
        spot_area = np.pi * (spot_diameter / 2)**2
        n_spots = int(area / spot_area) * 2  # Overlapping spots
    
    # Generate spot coordinates
    if aggregation == "hex":
        spot_coords = generate_hexagonal_spots(
            cell_coords, spot_diameter, n_spots
        )
    elif aggregation == "grid":
        spot_coords = generate_grid_spots(
            cell_coords, spot_diameter, n_spots
        )
    elif aggregation == "random":
        spot_coords = generate_random_spots(
            cell_coords, spot_diameter, n_spots, random_state
        )
    else:
        raise ValueError(f"Unknown aggregation method: {aggregation}")
    
    # Aggregate cells to spots
    spot_expression = aggregate_cells_to_spots(
        single_cell_adata, spot_coords, spot_diameter
    )
    
    # Create pseudo-Visium AnnData
    pseudo_visium = ad.AnnData(
        X=spot_expression,
        dtype=np.float32
    )
    pseudo_visium.var_names = single_cell_adata.var_names.copy()
    pseudo_visium.obs_names = [f"spot_{i}" for i in range(len(spot_coords))]
    pseudo_visium.obsm['spatial'] = spot_coords
    pseudo_visium.uns['spot_diameter'] = spot_diameter
    pseudo_visium.uns['aggregation'] = aggregation
    
    return pseudo_visium


def aggregate_cells_to_spots(
    cell_adata: ad.AnnData,
    spot_coords: np.ndarray,
    spot_diameter: float = 55.0
) -> np.ndarray:
    """
    Aggregate single-cell expression to spot-level.
    
    Parameters
    ----------
    cell_adata : AnnData
        Single-cell AnnData with spatial coordinates
    spot_coords : ndarray
        Spot coordinates (n_spots x 2)
    spot_diameter : float
        Spot diameter for cell assignment
        
    Returns
    -------
    spot_expression : ndarray
        Aggregated expression (n_spots x n_genes)
    """
    cell_coords = cell_adata.obsm['spatial']
    cell_expression = cell_adata.X
    
    if hasattr(cell_expression, 'toarray'):
        cell_expression = cell_expression.toarray()
    
    n_spots = len(spot_coords)
    n_genes = cell_adata.n_vars
    
    spot_expression = np.zeros((n_spots, n_genes))
    spot_counts = np.zeros(n_spots)
    
    # Build KDTree for efficient nearest neighbor search
    tree = KDTree(spot_coords)
    
    # Assign each cell to nearest spot within diameter
    for i, cell_pos in enumerate(cell_coords):
        # Find nearest spot
        dist, idx = tree.query(cell_pos, k=1)
        
        if dist <= spot_diameter / 2:
            spot_expression[idx] += cell_expression[i]
            spot_counts[idx] += 1
    
    # Normalize by number of cells per spot
    for i in range(n_spots):
        if spot_counts[i] > 0:
            spot_expression[i] /= spot_counts[i]
    
    return spot_expression


def generate_hexagonal_spots(
    cell_coords: np.ndarray,
    spot_diameter: float,
    n_spots: int
) -> np.ndarray:
    """
    Generate hexagonal spot arrangement.
    
    Parameters
    ----------
    cell_coords : ndarray
        Cell coordinates for bounding box
    spot_diameter : float
        Spot diameter
    n_spots : int
        Number of spots
        
    Returns
    -------
    spot_coords : ndarray
        Hexagonal spot coordinates
    """
    # Compute bounding box
    x_min, x_max = cell_coords[:, 0].min(), cell_coords[:, 0].max()
    y_min, y_max = cell_coords[:, 1].min(), cell_coords[:, 1].max()
    
    # Hexagonal grid spacing
    dx = spot_diameter * 0.866  # sqrt(3)/2
    dy = spot_diameter * 0.75
    
    # Generate grid
    n_cols = int((x_max - x_min) / dx) + 1
    n_rows = int((y_max - y_min) / dy) + 1
    
    spots = []
    for row in range(n_rows):
        for col in range(n_cols):
            x = x_min + col * dx
            y = y_min + row * dy
            
            # Offset every other row
            if row % 2 == 1:
                x += dx / 2
            
            spots.append([x, y])
    
    spot_coords = np.array(spots)
    
    # Limit to n_spots
    if len(spot_coords) > n_spots:
        # Keep spots near center
        center = np.mean(cell_coords, axis=0)
        dists = np.linalg.norm(spot_coords - center, axis=1)
        indices = np.argsort(dists)[:n_spots]
        spot_coords = spot_coords[indices]
    
    return spot_coords


def generate_grid_spots(
    cell_coords: np.ndarray,
    spot_diameter: float,
    n_spots: int
) -> np.ndarray:
    """
    Generate grid spot arrangement.
    
    Parameters
    ----------
    cell_coords : ndarray
        Cell coordinates for bounding box
    spot_diameter : float
        Spot diameter
    n_spots : int
        Number of spots
        
    Returns
    -------
    spot_coords : ndarray
        Grid spot coordinates
    """
    x_min, x_max = cell_coords[:, 0].min(), cell_coords[:, 0].max()
    y_min, y_max = cell_coords[:, 1].min(), cell_coords[:, 1].max()
    
    # Grid spacing
    spacing = spot_diameter
    
    n_cols = int((x_max - x_min) / spacing) + 1
    n_rows = int((y_max - y_min) / spacing) + 1
    
    spots = []
    for row in range(n_rows):
        for col in range(n_cols):
            x = x_min + col * spacing
            y = y_min + row * spacing
            spots.append([x, y])
    
    spot_coords = np.array(spots)
    
    if len(spot_coords) > n_spots:
        center = np.mean(cell_coords, axis=0)
        dists = np.linalg.norm(spot_coords - center, axis=1)
        indices = np.argsort(dists)[:n_spots]
        spot_coords = spot_coords[indices]
    
    return spot_coords


def generate_random_spots(
    cell_coords: np.ndarray,
    spot_diameter: float,
    n_spots: int,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Generate random spot arrangement.
    
    Parameters
    ----------
    cell_coords : ndarray
        Cell coordinates for bounding box
    spot_diameter : float
        Spot diameter
    n_spots : int
        Number of spots
    random_state : int, optional
        Random seed
        
    Returns
    -------
    spot_coords : ndarray
        Random spot coordinates
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    x_min, x_max = cell_coords[:, 0].min(), cell_coords[:, 0].max()
    y_min, y_max = cell_coords[:, 1].min(), cell_coords[:, 1].max()
    
    spot_coords = np.random.uniform(
        low=[x_min, y_min],
        high=[x_max, y_max],
        size=(n_spots, 2)
    )
    
    return spot_coords
