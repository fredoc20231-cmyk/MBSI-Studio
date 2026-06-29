"""Data QC & Preprocessing workspace."""

import streamlit as st

from app.components.page_utils import ensure_adata
from app.workspaces._helpers import demo_banner
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.workflows.preprocess import run_preprocess_workflow
from mbsi.workflows.qc import run_qc_workflow


def render():
    demo_banner()
    ensure_adata(show_warning=False)
    st.markdown("### Data QC & Preprocessing")
    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.QC_PREPROCESS.value]
    tab_labels = [s.replace("_", " ").title() for s in substeps]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.slider("Min counts", 0, 500, 10, key="ws_pre_min_counts")
        st.slider("Max mito %", 0, 100, 20, key="ws_pre_max_mito")
    with tabs[1]:
        st.selectbox("Normalization", ["log1p+scale", "SCTransform", "technology default"], key="ws_norm_method")
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
        tech = st.session_state.get("selected_technology", "")
        st.caption(f"Platform QC hints for: {tech or 'unknown'}")
        st.info("Platform-specific QC metrics shown after technology selection in Study Setup.")
    with tabs[6]:
        st.selectbox("FDR threshold", [0.05, 0.1, 0.01], key="ws_fdr")

    if st.button("Run QC & Preprocess (demo)", type="primary", key="ws_run_qc_preprocess"):
        adata = st.session_state.get("adata")
        tech = st.session_state.get("selected_technology", "")
        qc_run = run_qc_workflow(
            adata,
            min_counts=st.session_state.get("ws_pre_min_counts", 10),
            max_mito_pct=st.session_state.get("ws_pre_max_mito", 20),
            technology_key=tech,
        )
        pre_run = run_preprocess_workflow(adata, technology_key=tech)
        st.session_state.run_outputs["qc_preprocess"] = {
            "qc": qc_run.to_dict(),
            "preprocess": pre_run.to_dict(),
        }
        st.session_state.last_run = "QC & Preprocessing"
        st.toast("QC & preprocessing complete (demo).")
