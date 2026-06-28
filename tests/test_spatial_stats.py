"""Tests for spatial autocorrelation."""

from mbsi.analysis.clustering import full_clustering_workflow
from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.spatial_stats import (
    build_spatial_weights,
    morans_i,
    gearys_c,
    spatial_autocorrelation_table,
)


def _clustered():
    return full_clustering_workflow(
        make_synthetic_visium_adata(n_spots=50, n_genes=80, seed=4),
        n_top_genes=50,
        n_comps=8,
        n_neighbors=10,
        n_pcs=5,
        resolution=0.8,
    )


def test_build_spatial_weights():
    adata = make_synthetic_visium_adata(n_spots=20, seed=0)
    W = build_spatial_weights(adata, k=4)
    assert W.shape == (20, 20)
    assert W.nnz > 0


def test_morans_i_and_gearys_c():
    adata = _clustered()
    genes = adata.var_names[adata.var["highly_variable"]][:5].tolist()
    mi = morans_i(adata, genes, k=4)
    gc = gearys_c(adata, genes, k=4)
    assert len(mi) == len(genes)
    assert len(gc) == len(genes)
    assert "morans_i" in mi.columns
    assert "gearys_c" in gc.columns


def test_spatial_autocorrelation_table():
    adata = _clustered()
    table = spatial_autocorrelation_table(adata, n_top=20, k=4)
    assert not table.empty
    assert {"gene", "morans_i", "gearys_c"}.issubset(table.columns)
