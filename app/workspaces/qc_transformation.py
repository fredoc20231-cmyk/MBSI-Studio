"""QC & Transformation workspace."""

from __future__ import annotations

import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, require_adata
from mbsi.preprocessing import normalize
from mbsi.pseudobulk import run_pca_heatmap
from mbsi.qc import compute_original_summary, filter_data
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.visualization.seurat_like import plot_quilt


def render() -> None:
    st.markdown("### QC & Transformation")
    if not require_adata("qc_transformation"):
        return

    adata = st.session_state.adata
    tech_key = st.session_state.get("selected_technology", "") or st.session_state.get("mbsi_platform", "")
    tech = get_technology(tech_key)
    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.QC_TRANSFORMATION.value]
    tabs = st.tabs([s.replace("_", " ").title() for s in substeps])

    with tabs[0]:
        st.markdown("#### Original summary")
        summary = compute_original_summary(adata)
        st.dataframe(summary, use_container_width=True)
        safe_register_table("qc_transformation", "original_summary", summary)

    with tabs[1]:
        st.markdown("#### Filter data")
        st.caption("Order: samples → genes by name → spots/cells → genes by count")
        sample_ids = None
        if "sample_id" in adata.obs.columns:
            all_samples = adata.obs["sample_id"].astype(str).unique().tolist()
            sample_ids = st.multiselect("Sample filter", all_samples, default=all_samples, key="qct_sample_filter")
        gene_pat = st.text_input("Gene name filter (regex)", key="qct_gene_pat")
        c1, c2 = st.columns(2)
        min_counts = c1.number_input("Min counts", 0, 10000, 500, key="qct_min_counts")
        max_counts = c2.number_input("Max counts (0 = no max)", 0, 50000, 0, key="qct_max_counts")
        c3, c4 = st.columns(2)
        min_genes = c3.number_input("Min genes", 0, 500, 200, key="qct_min_genes")
        max_genes = c4.number_input("Max genes (0 = no max)", 0, 5000, 0, key="qct_max_genes")
        min_cells = st.number_input("Min cells expressing (gene filter)", 0, 100, 3, key="qct_min_cells")
        max_mito = st.slider("Mito threshold %", 0, 100, 20, key="qct_max_mito")
        if st.button("Apply filters", type="primary", key="qct_apply_filter"):
            filtered, filt_summary, warnings = filter_data(
                adata,
                sample_ids=sample_ids,
                gene_name_pattern=gene_pat,
                min_counts=min_counts,
                max_counts=max_counts if max_counts > 0 else None,
                min_genes=min_genes,
                max_genes=max_genes if max_genes > 0 else None,
                min_cells_expressing=min_cells,
                max_mito_pct=max_mito,
            )
            st.session_state.adata = filtered
            st.session_state.run_outputs["qc_transformation"] = {"filter_summary": filt_summary.to_dict()}
            for w in warnings:
                st.warning(w)
            st.success(f"Filtered to {filtered.n_obs} spots, {filtered.n_vars} genes.")
            st.rerun()

    with tabs[2]:
        st.markdown("#### Normalize")
        norm_options = ["log", "sctransform_like", "clr", "tfidf_lsi", "none"]
        if tech:
            st.caption(f"Technology default: {tech.normalization_strategy}")
        method = st.selectbox("Normalization method", norm_options, key="qct_norm_method")
        if st.button("Run normalization", key="qct_run_norm"):
            normalized, note = normalize(adata, method=method)
            st.session_state.adata = normalized
            st.info(note)
            st.rerun()

    with tabs[3]:
        st.markdown("#### Pseudobulk")
        group_opts = [c for c in ("sample_id", "condition", "replicate_id", "tissue_region", "cluster", "domain") if c in adata.obs.columns]
        groupby = st.selectbox("Aggregate by", group_opts or ["condition"], key="qct_pb_group")
        if st.button("Compute pseudobulk", key="qct_run_pb"):
            mat, pca_df, fig = run_pca_heatmap(adata, groupby=groupby)
            if not mat.empty:
                st.dataframe(mat.head(20), use_container_width=True)
            if not pca_df.empty:
                st.dataframe(pca_df, use_container_width=True)
            if fig is not None:
                render_interactive_plot(fig, key="qct_pb_heatmap")

    with tabs[4]:
        st.markdown("#### Quilt plot")
        quilt_feats = st.multiselect(
            "Features",
            [c for c in adata.obs.columns if c in ("total_counts", "n_genes_by_counts", "pct_counts_mt", "condition", "sample_id", "cluster", "domain")],
            default=[c for c in ("total_counts", "n_genes_by_counts", "pct_counts_mt") if c in adata.obs.columns],
            key="qct_quilt_feats",
        )
        fig = plot_quilt(adata, features=quilt_feats or None)
        render_interactive_plot(fig, key="qct_quilt_plot")

    render_continue("qc_transformation")
