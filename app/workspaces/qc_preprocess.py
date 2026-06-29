"""Data QC & Preprocessing workspace."""

import streamlit as st

from app.components.page_utils import load_advanced_demo_into_session
from app.workspaces._helpers import demo_banner
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.profiles.seurat_like import list_workflow_presets, get_workflow_preset
from mbsi.profiles.spatial_platforms import get_platform_workflow
from mbsi.references.marker_panels import list_panels
from mbsi.workflows.preprocess import run_preprocess_workflow
from mbsi.workflows.qc import run_qc_workflow

CLUSTERING_OPTIONS = [
    "Leiden",
    "Louvain",
    "k-means",
    "Spatial graph",
    "BayesSpace-style",
    "GraphST adapter mode",
    "STAGATE adapter mode",
]

MARKER_PANELS = [
    "Default immune (CD3D, CD8A, CD68, FOXP3)",
    "TME stroma (COL1A1, ACTA2, FAP, PDGFRA)",
    "Epithelial (EPCAM, KRT8, KRT18, MUC1)",
    "Custom (from session gene list)",
]


def render():
    st.markdown("### Data QC & Preprocessing")
    adata = st.session_state.get("adata")

    if adata is None:
        st.warning("QC & Preprocessing unavailable — upload real data first.")
        if st.button("Load Demo Dataset (labeled demo)", key="qc_load_demo"):
            load_advanced_demo_into_session(force=True)
            st.session_state.using_synthetic_demo = True
            st.session_state.mbsi_platform = "demo"
            st.rerun()
        return

    if st.session_state.get("using_synthetic_demo"):
        demo_banner()

    tech_key = st.session_state.get("selected_technology", "") or st.session_state.get("mbsi_platform", "")
    tech = get_technology(tech_key)
    platform_wf = get_platform_workflow(tech_key or "generic_h5ad")
    preset_options = list_workflow_presets()
    default_preset = platform_wf.get("default_preset", "basic_unsupervised")

    st.markdown("#### Workflow preset")
    preset_labels = {k: get_workflow_preset(k)["label"] for k in preset_options}
    st.selectbox(
        "Analysis workflow preset",
        preset_options,
        index=preset_options.index(default_preset) if default_preset in preset_options else 0,
        format_func=lambda k: preset_labels.get(k, k),
        key="ws_workflow_preset",
        help=get_workflow_preset(st.session_state.get("ws_workflow_preset", default_preset)).get("description", ""),
    )

    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.QC_PREPROCESS.value]
    tab_labels = [s.replace("_", " ").title() for s in substeps]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.slider("Min counts", 0, 5000, 500, key="ws_pre_min_counts")
        st.slider("Max mito %", 0, 100, 20, key="ws_pre_max_mito")
    with tabs[1]:
        default_norm = tech.normalization_strategy if tech else "log1p+scale"
        norm_options = platform_wf.get("normalization_options", ["log1p", "sctransform_like"])
        st.selectbox(
            "Normalization method",
            norm_options + ["technology default"],
            index=0,
            key="ws_norm_method",
            help=f"Technology default: {default_norm}",
        )
        st.number_input("HVG count", 500, 5000, 2000, step=100, key="ws_n_hvg")
    with tabs[2]:
        st.checkbox("Check batch effects across samples", value=True, key="ws_batch_check")
        st.checkbox("Compare replicates", value=True, key="ws_replicate_check")
    with tabs[3]:
        st.slider("Max mito % filter", 0, 100, 20, key="ws_mito_filter")
        st.slider("Min ribo % (optional)", 0, 100, 0, key="ws_ribo_filter")
    with tabs[4]:
        st.number_input("Min genes per spot", 0, 500, 200, key="ws_min_genes")
        st.number_input("Min spots per gene", 0, 100, 3, key="ws_min_spots_gene")
    with tabs[5]:
        st.caption(f"Platform QC hints for: {tech.label if tech else tech_key or 'unknown'}")
        if tech and tech.qc_metrics:
            for metric in tech.qc_metrics:
                st.markdown(f"- {metric}")
        else:
            st.info("Select a technology in Study Setup for platform-specific QC metrics.")
    with tabs[6]:
        st.selectbox("FDR threshold", [0.05, 0.1, 0.01], key="ws_fdr")
        st.selectbox("P-value threshold", [0.05, 0.01, 0.001], key="ws_pval")
        st.number_input("Log2FC threshold", 0.0, 4.0, 0.25, step=0.05, key="ws_log2fc")

    st.markdown("#### Clustering & marker panel")
    c1, c2 = st.columns(2)
    tech_choices = tech.clustering_choices if tech and tech.clustering_choices else CLUSTERING_OPTIONS
    with c1:
        st.selectbox("Clustering method", tech_choices + [o for o in CLUSTERING_OPTIONS if o not in tech_choices], key="ws_cluster_method")
    with c2:
        panel_names = list_panels()
        st.selectbox("Reference marker panel", panel_names + MARKER_PANELS, key="ws_marker_panel")

    if st.button("Run QC & Preprocess", type="primary", key="ws_run_qc_preprocess"):
        norm = st.session_state.get("ws_norm_method", "log1p")
        if norm == "technology default":
            norm = "log1p"
        qc_run = run_qc_workflow(
            adata,
            min_counts=st.session_state.get("ws_pre_min_counts", 500),
            min_genes=st.session_state.get("ws_min_genes", 200),
            max_mito_pct=st.session_state.get("ws_pre_max_mito", 20),
            technology_key=tech_key,
            workflow_preset=st.session_state.get("ws_workflow_preset", default_preset),
        )
        pre_run = run_preprocess_workflow(
            adata,
            technology_key=tech_key,
            clustering_method=st.session_state.get("ws_cluster_method", "Leiden"),
            marker_panel=st.session_state.get("ws_marker_panel", MARKER_PANELS[0]),
            fdr_threshold=st.session_state.get("ws_fdr", 0.05),
            normalization=norm,
            n_top_genes=int(st.session_state.get("ws_n_hvg", 2000)),
            workflow_preset=st.session_state.get("ws_workflow_preset", default_preset),
        )
        st.session_state.run_outputs["qc_preprocess"] = {
            "qc": qc_run.to_dict(),
            "preprocess": pre_run.to_dict(),
        }
        st.session_state.qc_settings = {
            "min_counts": st.session_state.get("ws_pre_min_counts"),
            "min_genes": st.session_state.get("ws_min_genes"),
            "max_mito_pct": st.session_state.get("ws_pre_max_mito"),
            "n_hvg": st.session_state.get("ws_n_hvg"),
            "normalization": norm,
            "workflow_preset": st.session_state.get("ws_workflow_preset"),
            "fdr": st.session_state.get("ws_fdr"),
            "pval": st.session_state.get("ws_pval"),
            "log2fc": st.session_state.get("ws_log2fc"),
            "clustering_method": st.session_state.get("ws_cluster_method"),
            "marker_panel": st.session_state.get("ws_marker_panel"),
            "technology_key": tech_key,
        }
        st.session_state.last_run = "QC & Preprocessing"
        for note in (pre_run.outputs.get("normalization_note"), pre_run.outputs.get("clustering_fallback")):
            if note:
                st.info(note)
        for w in qc_run.warnings + pre_run.warnings:
            if w:
                st.warning(w)
        st.toast("QC & preprocessing complete.")
