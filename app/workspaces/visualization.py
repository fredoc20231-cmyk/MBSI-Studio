"""Visualization workspace — spatial maps, reductions, violin/dot/heatmap."""

from __future__ import annotations

import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.workspaces._spatial_page import render_continue, render_page_header, require_adata
from mbsi.schema.technology import get_technology, is_milestone_platform
from mbsi.analysis.clustering import run_pca, run_umap
from mbsi.visualization.seurat_like import (
    plot_dotplot,
    plot_heatmap,
    plot_quilt,
    plot_spatial_feature,
    plot_umap_split,
    plot_violin,
)


def render() -> None:
    render_page_header(
        "Visualization",
        "Spatial maps, quilt plots, reductions, violin, dot, and heatmap views.",
        icon="📊",
    )
    if not require_adata("visualization"):
        return

    tech_key = st.session_state.get("selected_technology", "") or st.session_state.get("mbsi_platform", "")
    if tech_key and not is_milestone_platform(tech_key) and tech_key not in ("csv_matrix", "demo"):
        spec = get_technology(tech_key)
        label = spec.label if spec else tech_key
        st.warning(f"**{label}** is marked **Coming later** — not supported in Milestone 1.")
        return

    adata = st.session_state.adata
    tech_key = st.session_state.get("selected_technology", "") or st.session_state.get("mbsi_platform", "")
    analysis = st.session_state.get("analysis_results") or {}
    milestone_out = (st.session_state.get("run_outputs") or {}).get("milestone1_pipeline") or (
        (st.session_state.get("run_outputs") or {}).get("qc_transformation", {}).get("milestone_pipeline")
    )
    if analysis.get("status") == "success":
        emb = analysis.get("embedding") or {}
        clusters = analysis.get("clusters") or {}
        st.caption(
            f"Milestone 1 analysis loaded — UMAP: {'yes' if emb.get('has_umap') else 'no'}, "
            f"clusters: {clusters.get('n_clusters', 0)}"
        )
    if milestone_out and tech_key in ("visium", "xenium", "generic_h5ad"):
        with st.expander("Milestone 1 pipeline outputs", expanded=False):
            for label, path in milestone_out.items():
                st.caption(f"{label}: {path}")
    tabs = st.tabs(["Spatial", "Quilt", "Reduction", "Violin / Dot / Heatmap"])

    with tabs[0]:
        if "spatial" not in adata.obsm:
            st.warning("No spatial coordinates in adata.obsm['spatial'] — complete Study & Data ingest first.")
        obs_feats = [c for c in adata.obs.columns if c not in ("qc_pass",)]
        gene = st.selectbox("Feature", list(adata.var_names[:200]) + obs_feats, key="viz_feature")
        fig = plot_spatial_feature(adata, gene)
        render_interactive_plot(fig, key="viz_spatial")

    with tabs[1]:
        fig = plot_quilt(adata)
        render_interactive_plot(fig, key="viz_quilt")

    with tabs[2]:
        if "X_umap" in adata.obsm:
            st.caption("UMAP from Milestone 1 pipeline (obsm['X_umap']).")
        elif analysis.get("status") != "success":
            st.caption("Run **Start Analysis** on Study & Data to compute UMAP, or use the button below.")
        if "cluster" not in adata.obs.columns:
            if st.button("Compute PCA + UMAP + Leiden clusters", key="viz_run_cluster"):
                from mbsi.analysis.seurat_like import run_seurat_like_pipeline

                results = run_seurat_like_pipeline(
                    adata,
                    preset="spatial_transcriptomics",
                    min_counts=50,
                    min_genes=10,
                    max_mito=30.0,
                )
                st.session_state.adata = results["adata"]
                st.session_state.marker_table = results.get("markers")
                st.session_state.run_outputs["visualization"] = {
                    "n_clusters": results["adata"].obs["cluster"].nunique() if "cluster" in results["adata"].obs else 0,
                }
                st.rerun()
        if "X_umap" not in adata.obsm:
            if st.button("Compute PCA + UMAP", key="viz_run_umap"):
                adata = run_pca(adata)
                adata = run_umap(adata)
                st.session_state.adata = adata
                st.rerun()
        split_by = st.selectbox("Facet by", [c for c in ("sample_id", "condition", "replicate_id") if c in adata.obs.columns] or ["cluster"], key="viz_split")
        fig = plot_umap_split(adata, split_by=split_by)
        render_interactive_plot(fig, key="viz_umap")

    with tabs[3]:
        groupby = st.selectbox("Group by", [c for c in ("cluster", "domain", "condition") if c in adata.obs.columns] or ["cluster"], key="viz_group")
        qc_keys = [k for k in ("total_counts", "n_genes_by_counts", "pct_counts_mt") if k in adata.obs.columns]
        if qc_keys:
            fig = plot_violin(adata, qc_keys[:3], groupby=groupby)
            render_interactive_plot(fig, key="viz_violin")
        genes = st.multiselect("Genes for dotplot", list(adata.var_names[:50]), default=list(adata.var_names[:5]), key="viz_genes")
        if genes and groupby in adata.obs.columns:
            import pandas as pd
            import numpy as np

            rows = {}
            for grp in adata.obs[groupby].astype(str).unique():
                mask = adata.obs[groupby].astype(str) == grp
                sub = adata[mask]
                rows[grp] = [float(np.asarray(sub[:, g].X).mean()) for g in genes]
            mat = pd.DataFrame(rows, index=genes).T
            render_interactive_plot(plot_dotplot(mat), key="viz_dot")
            render_interactive_plot(plot_heatmap(mat), key="viz_heatmap")

    render_continue("visualization")
