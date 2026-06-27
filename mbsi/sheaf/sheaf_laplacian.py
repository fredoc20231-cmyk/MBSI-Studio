"""
Sheaf Laplacian construction for tissue-aware regularization.

Builds sheaf Laplacian operators that respect tissue compartment
boundaries and can incorporate restriction maps.
"""

from typing import Optional, Tuple

import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix, block_diag


def build_sheaf_laplacian(
    graph: nx.Graph,
    feature_dim: int,
    boundary_penalty: bool = True,
    use_restriction_maps: bool = False
) -> csr_matrix:
    """
    Build sheaf Laplacian from tissue graph.
    
    For the MVP, uses block-diagonal approximation of the graph Laplacian.
    Future versions can incorporate true restriction maps.
    
    Parameters
    ----------
    graph : nx.Graph
        Cell graph
    feature_dim : int
        Dimension of feature space (number of genes)
    boundary_penalty : bool
        If True, add penalty for edges crossing compartment boundaries
    use_restriction_maps : bool
        If True, use restriction maps (placeholder for future)
        
    Returns
    -------
    laplacian : csr_matrix
        Sheaf Laplacian matrix (n_cells * feature_dim x n_cells * feature_dim)
    """
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    
    # Build standard graph Laplacian
    L_graph = nx.laplacian_matrix(graph).toarray()
    
    # Check for boundary labels
    has_labels = all('label' in graph.nodes[i] for i in graph.nodes())
    
    if boundary_penalty and has_labels:
        # Increase penalty for boundary-crossing edges
        for i, j in graph.edges():
            if graph.nodes[i]['label'] != graph.nodes[j]['label']:
                # Increase weight for boundary edges
                L_graph[i, j] *= 2.0
                L_graph[j, i] *= 2.0
    
    # Build block-diagonal sheaf Laplacian
    # Each node gets a feature_dim x feature_dim block
    blocks = []
    
    for i in range(n_nodes):
        # Diagonal block: degree * identity
        degree = L_graph[i, i]
        blocks.append(degree * np.eye(feature_dim))
    
    # Off-diagonal blocks: -weight * identity
    for i, j in graph.edges():
        weight = graph[i][j].get('weight', 1.0)
        # Add off-diagonal blocks (simplified for MVP)
        # In full sheaf theory, these would be restriction maps
    
    # Build block diagonal Laplacian (MVP approximation)
    L_sheaf = block_diag(blocks)
    
    # Add off-diagonal terms for edges
    # For MVP: use simple coupling
    row_indices = []
    col_indices = []
    data = []
    
    for i, j in graph.edges():
        weight = graph[i][j].get('weight', 1.0)
        
        # Add coupling for all feature dimensions
        for f in range(feature_dim):
            row_idx = i * feature_dim + f
            col_idx = j * feature_dim + f
            
            row_indices.extend([row_idx, col_idx])
            col_indices.extend([col_idx, row_idx])
            data.extend([-weight, -weight])
    
    # Add to Laplacian
    L_offdiag = csr_matrix((data, (row_indices, col_indices)), 
                           shape=(n_nodes * feature_dim, n_nodes * feature_dim))
    
    L_sheaf = L_sheaf + L_offdiag
    
    return L_sheaf


def build_graph_laplacian(
    graph: nx.Graph,
    normalized: bool = False
) -> csr_matrix:
    """
    Build standard graph Laplacian (non-sheaf version).
    
    Parameters
    ----------
    graph : nx.Graph
        Cell graph
    normalized : bool
        If True, use normalized Laplacian
        
    Returns
    -------
    laplacian : csr_matrix
        Graph Laplacian matrix
    """
    if normalized:
        L = nx.normalized_laplacian_matrix(graph)
    else:
        L = nx.laplacian_matrix(graph)
    
    return L


def build_sheaf_coboundary(
    graph: nx.Graph,
    feature_dim: int,
    restriction_maps: Optional[dict] = None
) -> csr_matrix:
    """
    Build sheaf coboundary operator (placeholder for future).
    
    Parameters
    ----------
    graph : nx.Graph
        Cell graph
    feature_dim : int
        Feature dimension
    restriction_maps : dict, optional
        Restriction maps for each edge
        
    Returns
    -------
    coboundary : csr_matrix
        Coboundary operator
    """
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()
    
    # For MVP, use simple identity restriction maps
    # Full implementation would use actual restriction maps
    
    edge_list = list(graph.edges())
    
    row_indices = []
    col_indices = []
    data = []
    
    for e_idx, (i, j) in enumerate(edge_list):
        for f in range(feature_dim):
            # Coboundary maps nodes to edges
            row_idx = e_idx * feature_dim + f
            col_idx_i = i * feature_dim + f
            col_idx_j = j * feature_dim + f
            
            # Simple identity restriction
            row_indices.extend([row_idx, row_idx])
            col_indices.extend([col_idx_i, col_idx_j])
            data.extend([1.0, -1.0])
    
    coboundary = csr_matrix(
        (data, (row_indices, col_indices)),
        shape=(n_edges * feature_dim, n_nodes * feature_dim)
    )
    
    return coboundary


def compute_sheaf_laplacian_from_coboundary(
    coboundary: csr_matrix
) -> csr_matrix:
    """
    Compute sheaf Laplacian as coboundary^T @ coboundary.
    
    Parameters
    ----------
    coboundary : csr_matrix
        Coboundary operator
        
    Returns
    -------
    laplacian : csr_matrix
        Sheaf Laplacian
    """
    laplacian = coboundary.T @ coboundary
    return laplacian
