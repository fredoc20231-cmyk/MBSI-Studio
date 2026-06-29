"""Tests for batched sheaf regularization."""

import numpy as np

from mbsi.reconstruction.solver import apply_sheaf_regularization
from mbsi.sheaf.graph_builder import build_cell_graph


def test_sheaf_batch_matches_single_gene_loop():
    rng = np.random.default_rng(42)
    n_cells, n_genes = 20, 48
    coords = rng.random((n_cells, 2))
    graph = build_cell_graph(coords, k=4)
    expression = rng.random((n_cells, n_genes))

    batched = apply_sheaf_regularization(
        expression, graph, lambda_sheaf=0.15, gene_batch=16
    )
    per_gene = apply_sheaf_regularization(
        expression, graph, lambda_sheaf=0.15, gene_batch=1
    )
    np.testing.assert_allclose(batched, per_gene, rtol=1e-4, atol=1e-5)


def test_sheaf_batch_preserves_shape():
    n_cells, n_genes = 15, 10
    coords = np.random.randn(n_cells, 2)
    graph = build_cell_graph(coords, k=3)
    expression = np.random.rand(n_cells, n_genes)
    out = apply_sheaf_regularization(expression, graph, gene_batch=32)
    assert out.shape == expression.shape
