"""Spatial analysis page — QC through clustering, markers, and spatial statistics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.analysis.pipeline import run_standard_spatial_analysis, export_analysis_results, ANALYSIS_GUARDRAIL
from mbsi.analysis.clustering import run_pca, run_neighbors, run_leiden_clustering, run_umap
from mbsi.analysis.markers import rank_cluster_markers, top_markers_per_cluster, marker_expression_matrix
from mbsi.analysis.spatial_stats import spatial_autocorrelation_table
from mbsi.visualization.analysis_plots import (
    plot_pca_elbow,
    plot_pca_scatter,
    plot_umap,
    plot_spatial_clusters,
    plot_spatial_gene,
    plot_marker_dotplot,
    plot_morans_rank,
    plot_gearys_rank,
)

st.set_page_config(page_title="Analysis | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
ensure_adata(show_warning=True)

render_topnav(active="Analysis")

st.markdown("### Spatial Transcriptomics Analysis")
st.caption(ANALYSIS_GUARDRAIL)

ctrl, main = st.columns([1, 3])

with ctrl:
    st.markdown("**Analytical Controls**")
    min_counts = st.slider("Min counts", 0, 2000, 100, key="an_min_counts")
    min_genes = st.slider("Min genes", 0, 500, 50, key="an_min_genes")
    max_mito = st.slider("Max mito %", 0.0, 100.0, 25.0, key="an_max_mito")
    n_hvg = st.number_input("HVG count", 500, 5000, 2000, step=100, key="an_n_hvg")
    n_comps = st.slider("PCA components", 5, 50, 30, key="an_n_comps")
    n_neighbors = st.slider("Neighbors", 5, 100, 30, key="an_n_neighbors")
    n_pcs = st.slider("PCs for graph", 5, 30, 15, key="an_n_pcs")
    resolution = st.slider("Leiden resolution", 0.1, 2.0, 1.0, 0.1, key="an_res")
    spatial_top = st.number_input("Spatial stats genes", 20, 2000, 200, step=20, key="an_spatial_top")

    if st.button("Run Full Analysis", type="primary", key="an_full"):
        with st.spinner("Running standard spatial analysis..."):
            results = run_standard_spatial_analysis(
                st.session_state.adata,
                min_counts=min_counts,
                min_genes=min_genes,
                max_mito=max_mito,
                n_top_genes=int(n_hvg),
                n_comps=n_comps,
                n_neighbors=n_neighbors,
                n_pcs=n_pcs,
                resolution=resolution,
                spatial_stats_top_n=int(spatial_top),
            )
            st.session_state.analysis_results = results
            st.session_state.adata = results["adata"]
            st.session_state.marker_table = results["markers"]
            st.session_state.spatial_stats = results["spatial_stats"]
            export_analysis_results(results, out_dir=OUTPUT_DIR)
            st.session_state.last_run = "Full spatial analysis"
        st.success("Analysis complete.")

    if st.button("PCA + Cluster only", key="an_cluster"):
        adata = st.session_state.adata.copy()
        adata = run_pca(adata, n_comps=n_comps)
        adata = run_neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)
        adata = run_leiden_clustering(adata, resolution=resolution)
        adata = run_umap(adata)
        st.session_state.adata = adata
        st.session_state.last_run = "Clustering"
        st.success(f"{adata.obs['cluster'].nunique()} clusters found.")

    if st.button("Rank Markers", key="an_markers"):
        adata = st.session_state.adata
        if "cluster" not in adata.obs.columns:
            st.warning("Run clustering first.")
        else:
            markers = rank_cluster_markers(adata)
            st.session_state.marker_table = markers
            st.session_state.last_run = "Marker ranking"
            st.success(f"{len(markers)} marker rows computed.")

    if st.button("Spatial Statistics", key="an_spatial"):
        adata = st.session_state.adata
        stats = spatial_autocorrelation_table(adata, n_top=int(spatial_top))
        st.session_state.spatial_stats = stats
        st.session_state.last_run = "Spatial autocorrelation"
        st.success(f"Computed stats for {len(stats)} genes.")

with main:
    adata = st.session_state.adata
    if adata is None:
        st.info("No data loaded.")
        st.stop()

    t1, t2, t3, t4 = st.tabs(["Embeddings", "Spatial", "Markers", "Spatial Stats"])

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            if "X_pca" in adata.obsm:
                st.plotly_chart(plot_pca_elbow(adata), use_container_width=True, config={"displayModeBar": False})
                st.plotly_chart(plot_pca_scatter(adata), use_container_width=True, config={"displayModeBar": False})
        with c2:
            if "X_umap" in adata.obsm:
                st.plotly_chart(plot_umap(adata), use_container_width=True, config={"displayModeBar": False})

    with t2:
        if "cluster" in adata.obs.columns:
            st.plotly_chart(plot_spatial_clusters(adata), use_container_width=True, config={"displayModeBar": False})
        genes = [g for g in adata.var_names[:20]]
        gene = st.selectbox("Spatial gene", genes, key="an_gene")
        if gene:
            try:
                st.plotly_chart(plot_spatial_gene(adata, gene), use_container_width=True, config={"displayModeBar": False})
            except ValueError:
                st.warning("Gene not found in dataset.")

    with t3:
        markers = st.session_state.marker_table
        if markers is not None and not markers.empty:
            top = top_markers_per_cluster(markers, n=5)
            st.dataframe(top, use_container_width=True, hide_index=True)
            genes_top = top["gene"].unique().tolist()[:8]
            if genes_top and "cluster" in adata.obs.columns:
                mat = marker_expression_matrix(adata, genes_top)
                if not mat.empty:
                    st.plotly_chart(plot_marker_dotplot(mat), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Run marker ranking to see results.")

    with t4:
        stats = st.session_state.spatial_stats
        if stats is not None and not stats.empty:
            st.dataframe(stats.head(50), use_container_width=True, hide_index=True)
            s1, s2 = st.columns(2)
            with s1:
                st.plotly_chart(plot_morans_rank(stats), use_container_width=True, config={"displayModeBar": False})
            with s2:
                st.plotly_chart(plot_gearys_rank(stats), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Run spatial statistics to see Moran's I and Geary's C.")

    if st.session_state.analysis_results:
        with st.expander("Analysis parameters"):
            st.json(st.session_state.analysis_results.get("parameters", {}))

render_statusbar(show_actions=False)
