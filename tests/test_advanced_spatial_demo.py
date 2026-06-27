"""Tests for advanced spatial demo generator."""

from mbsi.demo.advanced_spatial_demo import generate_advanced_demo, CELL_TYPES


def test_generate_advanced_demo_keys():
    demo = generate_advanced_demo(n_cells=500, n_spots=50, plot_subset=200)
    assert demo["n_cells_total"] == 500
    assert len(demo["cell_types"]) == 10
    assert demo["histology_image"].shape[0] == 1024
    assert len(demo["cells"]) == 200
    assert demo["neighborhood_graph"].number_of_nodes() > 0
    assert len(demo["lr_pathways"]) >= 4
    assert demo["adata"] is not None
    assert demo["reconstructed"] is not None


def test_cell_types_count():
    assert len(CELL_TYPES) == 10
