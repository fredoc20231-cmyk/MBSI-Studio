#!/usr/bin/env python3
"""Smoke test UI plotting/data functions without launching Streamlit."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.components.layout import render_analysis_subtabs
    from app.components.demo_data import generate_dashboard_demo
    from app.components.histology import make_histology_overlay, make_ligand_gradient
    from app.components.network import neighborhood_graph, interactions_bar
    from app.components.cards import donut_composition, export_all
    from mbsi.analysis.demo import make_synthetic_visium_adata
    from mbsi.analysis.pipeline import run_standard_spatial_analysis
    from mbsi.visualization.analysis_plots import plot_umap, plot_spatial_clusters

    assert callable(render_analysis_subtabs)
    demo = generate_dashboard_demo(seed=42)
    make_histology_overlay(
        demo["histology_image"], demo["cells"],
        tissue_extent=demo["tissue_extent"],
        boundaries=demo["boundaries"],
    )
    make_ligand_gradient(demo["ligand_field"])
    neighborhood_graph(demo["network_nodes"], demo["network_edges"])
    interactions_bar(demo["interactions"])
    donut_composition(demo["composition"])
    export_all(demo, out_dir=ROOT / "data" / "outputs")

    synth = make_synthetic_visium_adata(n_spots=50, n_genes=100, seed=7)
    results = run_standard_spatial_analysis(
        synth, min_counts=0, min_genes=0, max_mito=100.0,
        n_top_genes=50, n_comps=8, n_neighbors=10, n_pcs=5, spatial_stats_top_n=20,
    )
    plot_umap(results["adata"])
    plot_spatial_clusters(results["adata"])

    from mbsi.communication import run_communication_analysis, make_communication_demo_adata
    from mbsi.visualization.communication_plots import plot_pathway_rankings

    comm = run_communication_analysis(make_communication_demo_adata(seed=7), k=5)
    plot_pathway_rankings(comm["pathway_rankings"])

    from mbsi.tme import run_tme_analysis, make_tme_demo_adata
    from mbsi.visualization.tme_plots import plot_niche_summary

    tme = run_tme_analysis(make_tme_demo_adata(seed=7))
    plot_niche_summary(tme["summary"])
    print("MBSI Studio UI smoke test passed.")


if __name__ == "__main__":
    main()
