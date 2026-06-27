"""
Sheaf-based regularization for reconstruction.

Computes regularization terms that enforce consistency across
tissue compartments and respect boundary structure.
"""

from typing import Optional

import numpy as np
from scipy.sparse import csr_matrix


def compute_sheaf_regularization(
    expression: np.ndarray,
    sheaf_laplacian: csr_matrix,
    lambda_sheaf: float = 0.1
) -> float:
    """
    Compute sheaf regularization term.
    
    Regularization: R = lambda_sheaf * x^T @ L @ x
    
    Parameters
    ----------
    expression : ndarray
        Flattened expression vector (n_cells * n_genes,)
    sheaf_laplacian : csr_matrix
        Sheaf Laplacian matrix
    lambda_sheaf : float
        Regularization strength
        
    Returns
    -------
    regularization : float
        Regularization value
    """
    # Compute quadratic form
    regularization = lambda_sheaf * float(expression @ (sheaf_laplacian @ expression))
    
    return regularization


def compute_sheaf_gradient(
    expression: np.ndarray,
    sheaf_laplacian: csr_matrix,
    lambda_sheaf: float = 0.1
) -> np.ndarray:
    """
    Compute gradient of sheaf regularization.
    
    Gradient: dR/dx = 2 * lambda_sheaf * L @ x
    
    Parameters
    ----------
    expression : ndarray
        Flattened expression vector
    sheaf_laplacian : csr_matrix
        Sheaf Laplacian matrix
    lambda_sheaf : float
        Regularization strength
        
    Returns
    -------
    gradient : ndarray
        Gradient vector
    """
    gradient = 2 * lambda_sheaf * (sheaf_laplacian @ expression)
    
    return gradient.toarray().flatten()


def compute_boundary_penalty(
    expression: np.ndarray,
    graph,
    labels: np.ndarray,
    lambda_boundary: float = 1.0
) -> float:
    """
    Compute penalty for expression inconsistency across boundaries.
    
    Parameters
    ----------
    expression : ndarray
        Expression matrix (n_cells x n_genes)
    graph : nx.Graph
        Cell graph
    labels : ndarray
        Compartment labels
    lambda_boundary : float
        Boundary penalty strength
        
    Returns
    -------
    penalty : float
        Boundary penalty value
    """
    from mbsi.sheaf.graph_builder import detect_boundaries
    
    boundary_edges = detect_boundaries(graph, labels)
    
    if len(boundary_edges) == 0:
        return 0.0
    
    penalty = 0.0
    
    for i, j in boundary_edges:
        # Penalize expression differences across boundary
        diff = expression[i] - expression[j]
        penalty += np.sum(diff**2)
    
    penalty = lambda_boundary * penalty / len(boundary_edges)
    
    return penalty


def compute_smoothness_regularization(
    expression: np.ndarray,
    graph,
    lambda_smooth: float = 0.1
) -> float:
    """
    Compute graph smoothness regularization.
    
    Encourages smooth expression across neighboring cells.
    
    Parameters
    ----------
    expression : ndarray
        Expression matrix (n_cells x n_genes)
    graph : nx.Graph
        Cell graph
    lambda_smooth : float
        Smoothness strength
        
    Returns
    -------
    regularization : float
        Smoothness regularization value
    """
    regularization = 0.0
    
    for i, j in graph.edges():
        weight = graph[i][j].get('weight', 1.0)
        diff = expression[i] - expression[j]
        regularization += weight * np.sum(diff**2)
    
    regularization = lambda_smooth * regularization / (2 * graph.number_of_edges())
    
    return regularization


def compute_total_regularization(
    expression: np.ndarray,
    sheaf_laplacian: csr_matrix,
    graph,
    labels: Optional[np.ndarray] = None,
    lambda_sheaf: float = 0.1,
    lambda_boundary: float = 1.0,
    lambda_smooth: float = 0.1
) -> dict:
    """
    Compute total regularization with multiple components.
    
    Parameters
    ----------
    expression : ndarray
        Expression matrix (n_cells x n_genes)
    sheaf_laplacian : csr_matrix
        Sheaf Laplacian
    graph : nx.Graph
        Cell graph
    labels : ndarray, optional
        Compartment labels
    lambda_sheaf : float
        Sheaf regularization strength
    lambda_boundary : float
        Boundary penalty strength
    lambda_smooth : float
        Smoothness strength
        
    Returns
    -------
    components : dict
        Dictionary with regularization components:
        - sheaf: sheaf regularization
        - boundary: boundary penalty
        - smoothness: smoothness regularization
        - total: sum of all components
    """
    n_cells, n_genes = expression.shape
    expression_flat = expression.flatten()
    
    # Sheaf regularization
    reg_sheaf = compute_sheaf_regularization(
        expression_flat, sheaf_laplacian, lambda_sheaf
    )
    
    # Boundary penalty
    if labels is not None:
        reg_boundary = compute_boundary_penalty(
            expression, graph, labels, lambda_boundary
        )
    else:
        reg_boundary = 0.0
    
    # Smoothness regularization
    reg_smooth = compute_smoothness_regularization(
        expression, graph, lambda_smooth
    )
    
    components = {
        "sheaf": reg_sheaf,
        "boundary": reg_boundary,
        "smoothness": reg_smooth,
        "total": reg_sheaf + reg_boundary + reg_smooth
    }
    
    return components
