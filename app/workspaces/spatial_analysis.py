"""Spatial analysis workspace — full QC through export pipeline."""

from __future__ import annotations

import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.components.page_utils import OUTPUT_DIR, init_session
from app.workspaces._helpers import add_finding, demo_banner, safe_register_finding, safe_register_table
from mbsi.analysis.pipeline import ANALYSIS_GUARDRAIL, export_analysis_results, run_standard_spatial_analysis
from mbsi.analysis.markers import marker_expression_matrix, top_markers_per_cluster
from mbsi.visualization.analysis_plots import (
    plot_counts_vs_mito,
    plot_gearys_rank,
    plot_marker_dotplot,
    plot_morans_rank,
    plot_pca_elbow,
    plot_pca_scatter,
    plot_qc_spatial,
    plot_qc_violin,
    plot_spatial_clusters,
    plot_spatial_gene,
    plot_umap,
)


def _ensure_adata():
    init_session()
    adata = st.session_state.get("adata")
    if adata is None:
        from mbsi.analysis.demo import make_synthetic_visium_adata
        adata = make_synthetic_visium_adata(n_spots=80, n_genes=150, seed=42)
        st.session_state.adata = adata
        st.session_state.using_synthetic_demo = True
        st.info("No uploaded data — using synthetic Visium for analysis demo.")
    return adata


def _run_full_analysis(adata, params: dict) -> None:
    with st.spinner("Running standard spatial analysis..."):
        try:
            results = run_standard_spatial_analysis(adata, **params)
            st.session_state.analysis_results = results
            st.session_state.adata = results["adata"]
            st.session_state.marker_table = results["markers"]
            st.session_state.spatial_stats = results["spatial_stats"]
            export_analysis_results(results, out_dir=OUTPUT_DIR)
            st.session_state.last_run = "Full spatial analysis"
            st.session_state.using_synthetic_demo = bool(st.session_state.get("using_synthetic_demo", False))

            safe_register_table("spatial_analysis", "qc_summary", results["qc_summary"])
            safe_register_table("spatial_analysis", "cluster_markers", results["markers"])
            safe_register_table("spatial_analysis", "spatial_autocorrelation", results["spatial_stats"])
            safe_register_finding(
                f"Analysis complete: {results['adata'].obs['cluster'].nunique()} clusters",
                section="spatial_analysis",
                module="spatial_analysis",
                title="Pipeline complete",
            )
            add_finding(
                "Spatial Analysis",
                f"{results['adata'].obs['cluster'].nunique()} clusters identified",
                module="spatial_analysis",
            )
            st.success("Analysis complete.")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")


def render():
    if st.session_state.get("using_synthetic_demo"):
        demo_banner()
    else:
        st.caption("Using uploaded data for spatial analysis.")

    platform = st.session_state.get("mbsi_platform", "unknown")
    readiness = st.session_state.get("mbsi_readiness", {})
    auto_run = st.session_state.pop("spatial_analysis_run_full", False)
    qc_only = st.session_state.get("spatial_analysis_qc_only", False)
    if platform and platform != "unknown":
        score = readiness.get("score") or st.session_state.get("ingestion_result", {}).get("readiness_score")
        cols = st.columns(3)
        cols[0].metric("Platform", platform)
        if score is not None:
            cols[1].metric("Readiness", f"{score}/100", readiness.get("status", ""))
        if auto_run:
            st.info("Data just uploaded — running full analysis with default parameters.")
        if qc_only:
            st.caption("QC-only mode — review QC tab after running analysis.")

    st.markdown("### Spatial Transcriptomics Analysis")
    st.caption(ANALYSIS_GUARDRAIL)

    adata = _ensure_adata()

    if auto_run:
        _run_full_analysis(
            adata,
            dict(
                min_counts=100,
                min_genes=50,
                max_mito=25.0,
                n_top_genes=2000,
                n_comps=30,
                n_neighbors=30,
                n_pcs=15,
                resolution=1.0,
                spatial_stats_top_n=200,
            ),
        )
        adata = st.session_state.get("adata") or adata
    ctrl, main = st.columns([1, 3], gap="small")

    with ctrl:
        st.markdown("**Analytical Controls**")
        min_counts = st.slider("Min counts", 0, 2000, 100, key="sa_min_counts")
        min_genes = st.slider("Min genes", 0, 500, 50, key="sa_min_genes")
        max_mito = st.slider("Max mito %", 0.0, 100.0, 25.0, key="sa_max_mito")
        n_hvg = st.number_input("HVG count", 500, 5000, 2000, step=100, key="sa_n_hvg")
        n_comps = st.slider("PCA components", 5, 50, 30, key="sa_n_comps")
        n_neighbors = st.slider("Neighbors", 5, 100, 30, key="sa_n_neighbors")
        n_pcs = st.slider("PCs for graph", 5, 30, 15, key="sa_n_pcs")
        resolution = st.slider("Leiden resolution", 0.1, 2.0, 1.0, 0.1, key="sa_res")
        spatial_top = st.number_input("Spatial stats genes", 20, 2000, 200, step=20, key="sa_spatial_top")

        params = dict(
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

        if st.button("Run Full Analysis", type="primary", key="sa_run_full"):
            _run_full_analysis(adata, params)

    with main:
        tabs = st.tabs(["QC", "PCA/UMAP", "Clusters", "Markers", "Spatial Stats", "Gene Viewer", "Export"])
        adata = st.session_state.get("adata") or adata

        with tabs[0]:
            if "total_counts" in adata.obs.columns:
                render_interactive_plot(plot_qc_violin(adata), title="QC Violin", module="spatial_analysis", key="sa_qc_violin")
                render_interactive_plot(plot_counts_vs_mito(adata), title="Counts vs Mito", module="spatial_analysis", key="sa_qc_mito")
                render_interactive_plot(plot_qc_spatial(adata, "total_counts"), title="Spatial Counts", module="spatial_analysis", key="sa_qc_spatial")
            else:
                st.info("Run analysis to compute QC metrics.")

        with tabs[1]:
            if "X_pca" in adata.obsm:
                render_interactive_plot(plot_pca_elbow(adata), title="PCA Elbow", module="spatial_analysis", key="sa_pca_elbow")
                render_interactive_plot(plot_pca_scatter(adata), title="PCA Scatter", module="spatial_analysis", key="sa_pca_scatter")
            if "X_umap" in adata.obsm:
                render_interactive_plot(plot_umap(adata), title="UMAP", module="spatial_analysis", key="sa_umap")
            if "X_pca" not in adata.obsm and "X_umap" not in adata.obsm:
                st.info("Run full analysis to generate embeddings.")

        with tabs[2]:
            if "cluster" in adata.obs.columns:
                render_interactive_plot(plot_spatial_clusters(adata), title="Spatial Clusters", module="spatial_analysis", key="sa_clusters")
                st.dataframe(adata.obs["cluster"].value_counts().rename("n_spots"), use_container_width=True)
            else:
                st.info("Run clustering via full analysis.")

        with tabs[3]:
            markers = st.session_state.get("marker_table")
            if markers is not None and not markers.empty:
                top = top_markers_per_cluster(markers, n=5)
                safe_register_table("spatial_analysis", "top_markers", top)
                st.dataframe(top, use_container_width=True, hide_index=True)
                genes_top = top["gene"].unique().tolist()[:8]
                if genes_top and "cluster" in adata.obs.columns:
                    mat = marker_expression_matrix(adata, genes_top)
                    if not mat.empty:
                        render_interactive_plot(
                            plot_marker_dotplot(mat), title="Marker Dotplot", module="spatial_analysis", key="sa_markers"
                        )
            else:
                st.info("Run full analysis to rank cluster markers.")

        with tabs[4]:
            stats = st.session_state.get("spatial_stats")
            if stats is not None and not stats.empty:
                st.dataframe(stats.head(50), use_container_width=True, hide_index=True)
                c1, c2 = st.columns(2)
                with c1:
                    render_interactive_plot(plot_morans_rank(stats), title="Moran's I", module="spatial_analysis", key="sa_morans")
                with c2:
                    render_interactive_plot(plot_gearys_rank(stats), title="Geary's C", module="spatial_analysis", key="sa_gearys")
            else:
                st.info("Run full analysis for spatial autocorrelation.")

        with tabs[5]:
            genes = list(adata.var_names[:50])
            if genes:
                gene = st.selectbox("Gene", genes, key="sa_gene_viewer")
                if gene and "spatial" in adata.obsm:
                    try:
                        render_interactive_plot(
                            plot_spatial_gene(adata, gene), title=f"Gene {gene}", module="spatial_analysis", key="sa_gene"
                        )
                    except ValueError:
                        st.warning("Gene not found.")
            else:
                st.info("No genes available.")

        with tabs[6]:
            results = st.session_state.get("analysis_results")
            if results:
                st.success(f"Exported to `{OUTPUT_DIR}`")
                if st.button("Re-export analysis results", key="sa_reexport"):
                    export_analysis_results(results, out_dir=OUTPUT_DIR)
                    st.toast("Export complete.")
                with st.expander("Analysis parameters"):
                    st.json(results.get("parameters", {}))
            else:
                st.info("Run full analysis to enable export.")
