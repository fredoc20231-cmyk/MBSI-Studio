"""
Tests for sheaf module.
"""

import pytest
import numpy as np
import networkx as nx


def test_build_cell_graph():
    """Test cell graph construction."""
    from mbsi.sheaf.graph_builder import build_cell_graph
    
    n_cells = 20
    coords = np.random.randn(n_cells, 2)
    
    graph = build_cell_graph(coords, k=5)
    
    # Check graph properties
    assert graph.number_of_nodes() == n_cells
    assert graph.number_of_edges() > 0
    
    # Check node positions
    for i in range(n_cells):
        assert i in graph.nodes
        assert 'pos' in graph.nodes[i]
        assert graph.nodes[i]['pos'].shape == (2,)


def test_build_sheaf_laplacian():
    """Test sheaf Laplacian construction."""
    from mbsi.sheaf.graph_builder import build_cell_graph
    from mbsi.sheaf.sheaf_laplacian import build_sheaf_laplacian
    
    n_cells = 15
    feature_dim = 10
    coords = np.random.randn(n_cells, 2)
    
    graph = build_cell_graph(coords, k=5)
    laplacian = build_sheaf_laplacian(graph, feature_dim)
    
    # Check shape
    expected_shape = (n_cells * feature_dim, n_cells * feature_dim)
    assert laplacian.shape == expected_shape
    
    # Check symmetry
    laplacian_dense = laplacian.toarray()
    assert np.allclose(laplacian_dense, laplacian_dense.T, atol=1e-6)


def test_sheaf_regularization():
    """Test sheaf regularization computation."""
    from mbsi.sheaf.graph_builder import build_cell_graph
    from mbsi.sheaf.sheaf_laplacian import build_sheaf_laplacian
    from mbsi.sheaf.regularizer import compute_sheaf_regularization
    
    n_cells = 10
    n_genes = 5
    coords = np.random.randn(n_cells, 2)
    
    graph = build_cell_graph(coords, k=3)
    laplacian = build_sheaf_laplacian(graph, n_genes)
    
    expression = np.random.randn(n_cells * n_genes)
    
    reg = compute_sheaf_regularization(expression, laplacian, lambda_sheaf=0.1)
    
    # Should be non-negative
    assert reg >= 0
    assert isinstance(reg, float)
