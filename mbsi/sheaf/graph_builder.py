"""
Graph construction for tissue-based sheaf regularization.

Builds cell graphs from spatial coordinates with optional
boundary labels for compartment-aware regularization.
"""

from typing import Optional, List

import numpy as np
import networkx as nx
from scipy.spatial import KDTree

from mbsi.utils import build_knn_graph


def build_cell_graph(
    coords: np.ndarray,
    k: int = 8,
    distance_threshold: Optional[float] = None,
    boundary_labels: Optional[np.ndarray] = None
) -> nx.Graph:
    """
    Build k-nearest neighbor graph from cell coordinates.
    
    Parameters
    ----------
    coords : ndarray
        Cell coordinates (n_cells x 2)
    k : int
        Number of nearest neighbors
    distance_threshold : float, optional
        Maximum edge distance. If None, no threshold.
    boundary_labels : ndarray, optional
        Boundary/compartment labels for each cell (n_cells,)
        
    Returns
    -------
    graph : nx.Graph
        NetworkX graph with nodes as cell indices and edges as kNN connections
    """
    n_cells = coords.shape[0]
    
    # Build kNN graph
    distances, indices = build_knn_graph(coords, k=k)
    
    # Create graph
    graph = nx.Graph()
    
    # Add nodes
    for i in range(n_cells):
        graph.add_node(i, pos=coords[i])
        if boundary_labels is not None:
            graph.nodes[i]['label'] = boundary_labels[i]
    
    # Add edges
    for i in range(n_cells):
        for j_idx, j in enumerate(indices[i]):
                dist = distances[i, j_idx]
                
                # Apply distance threshold if specified
                if distance_threshold is None or dist <= distance_threshold:
                    # Check if edge already exists (undirected graph)
                    if not graph.has_edge(i, j):
                        graph.add_edge(i, j, weight=dist)
    
    return graph


def build_delaunay_graph(
    coords: np.ndarray,
    boundary_labels: Optional[np.ndarray] = None
) -> nx.Graph:
    """
    Build Delaunay triangulation graph from coordinates.
    
    Parameters
    ----------
    coords : ndarray
        Cell coordinates (n_cells x 2)
    boundary_labels : ndarray, optional
        Boundary/compartment labels
        
    Returns
    -------
    graph : nx.Graph
        Delaunay triangulation graph
    """
    from scipy.spatial import Delaunay
    
    n_cells = coords.shape[0]
    
    # Compute Delaunay triangulation
    tri = Delaunay(coords)
    
    # Create graph
    graph = nx.Graph()
    
    # Add nodes
    for i in range(n_cells):
        graph.add_node(i, pos=coords[i])
        if boundary_labels is not None:
            graph.nodes[i]['label'] = boundary_labels[i]
    
    # Add edges from triangulation
    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            for j in range(i + 1, 3):
                edge = tuple(sorted([simplex[i], simplex[j]]))
                edges.add(edge)
    
    for i, j in edges:
        dist = np.linalg.norm(coords[i] - coords[j])
        graph.add_edge(i, j, weight=dist)
    
    return graph


def build_radius_graph(
    coords: np.ndarray,
    radius: float,
    boundary_labels: Optional[np.ndarray] = None
) -> nx.Graph:
    """
    Build radius-based graph (connect points within radius).
    
    Parameters
    ----------
    coords : ndarray
        Cell coordinates (n_cells x 2)
    radius : float
        Connection radius
    boundary_labels : ndarray, optional
        Boundary/compartment labels
        
    Returns
    -------
    graph : nx.Graph
        Radius graph
    """
    n_cells = coords.shape[0]
    
    # Use KDTree for efficient radius search
    tree = KDTree(coords)
    
    # Create graph
    graph = nx.Graph()
    
    # Add nodes
    for i in range(n_cells):
        graph.add_node(i, pos=coords[i])
        if boundary_labels is not None:
            graph.nodes[i]['label'] = boundary_labels[i]
    
    # Add edges
    for i in range(n_cells):
        neighbors = tree.query_ball_point(coords[i], radius)
        for j in neighbors:
            if i < j:  # Avoid duplicates and self-loops
                dist = np.linalg.norm(coords[i] - coords[j])
                graph.add_edge(i, j, weight=dist)
    
    return graph


def detect_boundaries(
    graph: nx.Graph,
    labels: np.ndarray
) -> List[tuple]:
    """
    Detect boundary edges between different compartments.
    
    Parameters
    ----------
    graph : nx.Graph
        Cell graph
    labels : ndarray
        Compartment labels for each node
        
    Returns
    -------
    boundary_edges : list
        List of edges (i, j) that cross compartment boundaries
    """
    boundary_edges = []
    
    for i, j in graph.edges():
        if labels[i] != labels[j]:
            boundary_edges.append((i, j))
    
    return boundary_edges


def partition_graph_by_labels(
    graph: nx.Graph,
    labels: np.ndarray
) -> dict:
    """
    Partition graph into subgraphs by compartment labels.
    
    Parameters
    ----------
    graph : nx.Graph
        Cell graph
    labels : ndarray
        Compartment labels
        
    Returns
    -------
    subgraphs : dict
        Dictionary mapping label to subgraph
    """
    unique_labels = np.unique(labels)
    subgraphs = {}
    
    for label in unique_labels:
        nodes = np.where(labels == label)[0]
        subgraph = graph.subgraph(nodes).copy()
        subgraphs[label] = subgraph
    
    return subgraphs
