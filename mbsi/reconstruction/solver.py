"""
Main MBSI reconstruction solver.

Combines diffusion kernel, optimal transport, and sheaf regularization
to reconstruct single-cell expression from spot-level data.
"""

from typing import Optional, Dict, Any
import json

import anndata as ad
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
from scipy.spatial.distance import cdist

from mbsi.diffusion.kernel import build_diffusion_kernel, build_euclidean_kernel
from mbsi.transport.unbalanced_ot import solve_unbalanced_ot
from mbsi.sheaf.graph_builder import build_cell_graph
from mbsi.sheaf.sheaf_laplacian import build_graph_laplacian
from mbsi.morphology.diffusion_tensor import build_tensor_field
from mbsi.reconstruction.transport_sparse import (
    apply_transport_to_expression,
    compress_transport_plan,
)


def run_mbsi(
    spot_adata: ad.AnnData,
    cell_coords: Optional[np.ndarray] = None,
    image: Optional[np.ndarray] = None,
    n_cells_per_spot: int = 5,
    gamma: float = 1.0,
    epsilon: float = 0.05,
    lambda_sheaf: float = 0.1,
    rho1: float = 1.0,
    rho2: float = 1.0,
    max_iter: int = 300,
    use_sheaf: bool = True,
    use_anisotropic: bool = True,
    k_graph: int = 8,
    top_k_transport: int = 50,
    sheaf_gene_batch: int = 32,
    random_state: Optional[int] = None
) -> ad.AnnData:
    """
    Run MBSI reconstruction to deconvolve spot-level expression to cell-level.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level AnnData with spatial coordinates in obsm['spatial']
    cell_coords : ndarray, optional
        Cell coordinates (n_cells x 2). If None, generates pseudo-cells.
    image : ndarray, optional
        Tissue image for morphology-aware diffusion
    n_cells_per_spot : int
        Number of cells to generate per spot (if cell_coords is None)
    gamma : float
        Kernel scale parameter
    epsilon : float
        OT entropy regularization
    lambda_sheaf : float
        Sheaf regularization strength
    rho1, rho2 : float
        Unbalanced OT marginal relaxation parameters
    max_iter : int
        Maximum iterations for optimization
    use_sheaf : bool
        If True, use sheaf regularization
    use_anisotropic : bool
        If True, use anisotropic diffusion kernel
    k_graph : int
        Number of neighbors for cell graph
    top_k_transport : int
        Retain only top-k OT edges per spot in uns['transport_plan'] (sparse storage)
    sheaf_gene_batch : int
        Number of genes solved per sheaf linear-system batch
    random_state : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    reconstructed_adata : AnnData
        Reconstructed cell-level AnnData with:
        - X: reconstructed expression (n_cells x n_genes)
        - obsm['spatial']: cell coordinates
        - uns['parameters']: reconstruction parameters
        - uns['convergence']: convergence log
    """
    if random_state is not None:
        np.random.seed(random_state)

    if "spatial" not in spot_adata.obsm:
        raise ValueError(
            "MBSI requires adata.obsm['spatial']. "
            "Upload spatial coordinates or use mbsi/io ingestion."
        )

    # Extract spot data
    spot_coords = spot_adata.obsm['spatial']
    spot_expression = spot_adata.X
    if hasattr(spot_expression, "toarray"):
        spot_expression = spot_expression.toarray()
    n_spots, n_genes = spot_expression.shape
    
    # Generate cell coordinates if not provided
    if cell_coords is None:
        cell_coords = generate_pseudo_cells(
            spot_coords, 
            n_cells_per_spot=n_cells_per_spot,
            random_state=random_state
        )
    
    n_cells = cell_coords.shape[0]
    
    # Build diffusion kernel
    if use_anisotropic and image is not None:
        tensor_field = build_tensor_field(spot_coords, image)
        kernel = build_diffusion_kernel(
            cell_coords, spot_coords, tensor_field, gamma=gamma
        )
    else:
        # Use Euclidean kernel as baseline
        kernel = build_euclidean_kernel(spot_coords, cell_coords, sigma=gamma)
    
    # Build cost matrix for OT (inverse of kernel)
    cost_matrix = 1.0 / (kernel + 1e-10)
    
    # Initialize distributions
    a = np.ones(n_spots) / n_spots
    b = np.ones(n_cells) / n_cells
    
    # Solve optimal transport
    transport_plan, ot_log = solve_unbalanced_ot(
        a, b, cost_matrix,
        epsilon=epsilon,
        rho1=rho1,
        rho2=rho2,
        max_iter=max_iter
    )
    
    # Reconstruct cell expression using transport plan
    reconstructed_expression = apply_transport_to_expression(spot_expression, transport_plan)

    # Apply sheaf Laplacian regularization when enabled (see apply_sheaf_regularization)
    if use_sheaf and lambda_sheaf > 0:
        graph = build_cell_graph(cell_coords, k=k_graph)
        reconstructed_expression = apply_sheaf_regularization(
            reconstructed_expression,
            graph,
            lambda_sheaf=lambda_sheaf,
            max_iter=50,
            gene_batch=sheaf_gene_batch,
        )
    
    # Create output AnnData
    reconstructed_adata = ad.AnnData(
        X=reconstructed_expression,
        dtype=np.float32
    )
    reconstructed_adata.var_names = spot_adata.var_names.copy()
    reconstructed_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    reconstructed_adata.obsm['spatial'] = cell_coords
    
    # Store parameters and convergence
    reconstructed_adata.uns['parameters'] = {
        'n_cells_per_spot': n_cells_per_spot,
        'gamma': gamma,
        'epsilon': epsilon,
        'lambda_sheaf': lambda_sheaf,
        'rho1': rho1,
        'rho2': rho2,
        'max_iter': max_iter,
        'use_sheaf': use_sheaf,
        'use_anisotropic': use_anisotropic,
        'k_graph': k_graph,
        'top_k_transport': top_k_transport,
        'sheaf_gene_batch': sheaf_gene_batch,
    }

    reconstructed_adata.uns['convergence'] = ot_log
    reconstructed_adata.uns['transport_plan'] = compress_transport_plan(
        transport_plan, top_k=top_k_transport
    )

    return reconstructed_adata


def generate_pseudo_cells(
    spot_coords: np.ndarray,
    n_cells_per_spot: int = 5,
    radius: float = 0.3,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Generate pseudo-cell coordinates inside each spot.
    
    Parameters
    ----------
    spot_coords : ndarray
        Spot coordinates (n_spots x 2)
    n_cells_per_spot : int
        Number of cells per spot
    radius : float
        Radius around spot center for cell placement
    random_state : int, optional
        Random seed
        
    Returns
    -------
    cell_coords : ndarray
        Cell coordinates (n_spots * n_cells_per_spot x 2)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n_spots = spot_coords.shape[0]
    n_cells = n_spots * n_cells_per_spot
    
    cell_coords = np.zeros((n_cells, 2))
    
    for i in range(n_spots):
        spot_center = spot_coords[i]
        start_idx = i * n_cells_per_spot
        
        # Generate cells around spot center
        angles = np.random.uniform(0, 2 * np.pi, n_cells_per_spot)
        radii = np.random.uniform(0, radius, n_cells_per_spot)
        
        for j in range(n_cells_per_spot):
            cell_coords[start_idx + j, 0] = spot_center[0] + radii[j] * np.cos(angles[j])
            cell_coords[start_idx + j, 1] = spot_center[1] + radii[j] * np.sin(angles[j])
    
    return cell_coords


def apply_sheaf_regularization(
    expression: np.ndarray,
    graph,
    lambda_sheaf: float = 0.1,
    max_iter: int = 50,
    tol: float = 1e-5,
    gene_batch: int = 32,
) -> np.ndarray:
    """
    Minimize 0.5||X - X0||^2 + 0.5 * lambda * tr(X^T L X).

    Closed-form solve via graph/sheaf Laplacian (``mbsi.sheaf.sheaf_laplacian``);
    objective matches ``mbsi.sheaf.regularizer.compute_sheaf_regularization``.
    Factorizes (I + lambda * L) once and solves gene RHS in batches.
    """
    if lambda_sheaf <= 0:
        return np.asarray(expression, dtype=np.float32)

    if hasattr(expression, "toarray"):
        expression = expression.toarray()

    x0 = np.asarray(expression, dtype=np.float64)
    laplacian = build_graph_laplacian(graph).tocsr()
    n_cells, n_genes = x0.shape
    identity = scipy.sparse.eye(n_cells, format="csr")
    system = (identity + lambda_sheaf * laplacian).tocsc()
    lu = scipy.sparse.linalg.splu(system)

    smoothed = np.zeros_like(x0)
    batch = max(1, int(gene_batch))
    for start in range(0, n_genes, batch):
        end = min(start + batch, n_genes)
        smoothed[:, start:end] = lu.solve(x0[:, start:end])

    return smoothed.astype(np.float32)


def apply_graph_smoothing(
    expression: np.ndarray,
    graph,
    lambda_sheaf: float = 0.1,
    max_iter: int = 50
) -> np.ndarray:
    """Backward-compatible alias for sheaf Laplacian regularization."""
    return apply_sheaf_regularization(
        expression, graph, lambda_sheaf=lambda_sheaf, max_iter=max_iter
    )


def run_iterative_mbsi(
    spot_adata: ad.AnnData,
    cell_coords: Optional[np.ndarray] = None,
    image: Optional[np.ndarray] = None,
    n_cells_per_spot: int = 5,
    gamma: float = 1.0,
    epsilon: float = 0.05,
    lambda_sheaf: float = 0.1,
    rho1: float = 1.0,
    rho2: float = 1.0,
    max_outer_iter: int = 10,
    max_inner_iter: int = 50,
    use_sheaf: bool = True,
    use_anisotropic: bool = True,
    k_graph: int = 8,
    top_k_transport: int = 50,
    sheaf_gene_batch: int = 32,
    random_state: Optional[int] = None
) -> ad.AnnData:
    """
    Run iterative MBSI with alternating OT and sheaf optimization.
    
    More sophisticated version that alternates between:
    1. OT with fixed expression
    2. Sheaf regularization with fixed transport
    
    Parameters
    ----------
    Same as run_mbsi, plus:
    max_outer_iter : int
        Number of outer iterations (alternating steps)
    max_inner_iter : int
        Number of inner iterations per step
        
    Returns
    -------
    reconstructed_adata : AnnData
        Reconstructed cell-level AnnData
    """
    if random_state is not None:
        np.random.seed(random_state)

    if "spatial" not in spot_adata.obsm:
        raise ValueError(
            "MBSI requires adata.obsm['spatial']. "
            "Upload spatial coordinates or use mbsi/io ingestion."
        )

    spot_coords = spot_adata.obsm['spatial']
    spot_expression = spot_adata.X
    if hasattr(spot_expression, 'toarray'):
        spot_expression = spot_expression.toarray()
    n_spots = spot_expression.shape[0]
    n_genes = spot_expression.shape[1]

    if cell_coords is None:
        cell_coords = generate_pseudo_cells(
            spot_coords,
            n_cells_per_spot=n_cells_per_spot,
            random_state=random_state
        )
    n_cells = cell_coords.shape[0]

    if use_anisotropic and image is not None:
        tensor_field = build_tensor_field(spot_coords, image)
        kernel = build_diffusion_kernel(
            cell_coords, spot_coords, tensor_field, gamma=gamma
        )
    else:
        kernel = build_euclidean_kernel(spot_coords, cell_coords, sigma=gamma)

    cost_matrix = 1.0 / (kernel + 1e-10)
    a = np.ones(n_spots) / n_spots
    b = np.ones(n_cells) / n_cells

    graph = build_cell_graph(cell_coords, k=k_graph) if use_sheaf and lambda_sheaf > 0 else None
    reconstructed_expression = None
    transport_plan = None
    ot_log = {}

    for _ in range(max_outer_iter):
        transport_plan, ot_log = solve_unbalanced_ot(
            a, b, cost_matrix,
            epsilon=epsilon,
            rho1=rho1,
            rho2=rho2,
            max_iter=max_inner_iter
        )
        reconstructed_expression = apply_transport_to_expression(spot_expression, transport_plan)
        if graph is not None and lambda_sheaf > 0:
            reconstructed_expression = apply_sheaf_regularization(
                reconstructed_expression,
                graph,
                lambda_sheaf=lambda_sheaf,
                max_iter=max_inner_iter,
                gene_batch=sheaf_gene_batch,
            )

    reconstructed_adata = ad.AnnData(
        X=reconstructed_expression.astype(np.float32),
        dtype=np.float32
    )
    reconstructed_adata.var_names = spot_adata.var_names.copy()
    reconstructed_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    reconstructed_adata.obsm['spatial'] = cell_coords
    reconstructed_adata.uns['parameters'] = {
        'n_cells_per_spot': n_cells_per_spot,
        'gamma': gamma,
        'epsilon': epsilon,
        'lambda_sheaf': lambda_sheaf,
        'rho1': rho1,
        'rho2': rho2,
        'max_outer_iter': max_outer_iter,
        'max_inner_iter': max_inner_iter,
        'use_sheaf': use_sheaf,
        'use_anisotropic': use_anisotropic and image is not None,
        'k_graph': k_graph,
        'top_k_transport': top_k_transport,
        'sheaf_gene_batch': sheaf_gene_batch,
        'iterative': True
    }
    reconstructed_adata.uns['convergence'] = ot_log
    if transport_plan is not None:
        reconstructed_adata.uns['transport_plan'] = compress_transport_plan(
            transport_plan, top_k=top_k_transport
        )

    return reconstructed_adata
