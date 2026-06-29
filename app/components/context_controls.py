"""Module-specific ribbon context controls."""

from __future__ import annotations

import streamlit as st

from app.components.module_registry import get_module, resolve_module
from app.components.page_utils import OUTPUT_DIR


def _ribbon_start() -> None:
    st.markdown('<div class="saas-ribbon">', unsafe_allow_html=True)


def _ribbon_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def _ribbon_item(label: str, widget_fn) -> None:
    st.markdown(f'<div class="saas-ribbon-item"><span class="saas-ribbon-label">{label}</span>', unsafe_allow_html=True)
    widget_fn()
    st.markdown("</div>", unsafe_allow_html=True)


def render_benchmark_ribbon() -> None:
    _ribbon_start()
    cols = st.columns([1.1, 1.0, 1.0, 0.7, 1.1, 0.7], gap="small")
    with cols[0]:
        st.selectbox("Dataset", ["synthetic_visium", "xenium_demo", "cosmx_demo"], key="rb_benchmark_dataset", label_visibility="visible")
    with cols[1]:
        st.selectbox("Platform", ["xenium", "cosmx", "merfish"], key="ctx_benchmark_platform", label_visibility="visible")
    with cols[2]:
        st.multiselect("Methods", ["mbsi", "tangram", "cell2location"], default=["mbsi", "tangram"], key="rb_benchmark_methods", label_visibility="visible")
    with cols[3]:
        st.number_input("Spots", min_value=20, max_value=500, value=40, step=10, key="rb_benchmark_spots", label_visibility="visible")
    with cols[4]:
        if st.button("Run Benchmark", key="rb_run_benchmark", type="primary", use_container_width=True):
            st.session_state.ribbon_action = "run_benchmark"
            st.rerun()
    with cols[5]:
        if st.button("Export", key="rb_export_benchmark", use_container_width=True):
            st.session_state.ribbon_action = "export_benchmark"
            st.rerun()
    _ribbon_end()


def render_discovery_ribbon() -> None:
    _ribbon_start()
    cols = st.columns([1.0, 0.9, 1.1, 1.2, 0.8], gap="small")
    with cols[0]:
        st.text_input("Cell Type Key", value="cell_type", key="rb_discovery_cell_key", label_visibility="visible")
    with cols[1]:
        st.slider("Diffusion", 0.0, 1.0, 0.5, 0.05, key="rb_discovery_diffusion", label_visibility="visible")
    with cols[2]:
        st.checkbox("Use Reconstruction", value=True, key="rb_discovery_use_recon", label_visibility="visible")
    with cols[3]:
        if st.button("Run Discovery", key="rb_run_discovery", type="primary", use_container_width=True):
            st.session_state.ribbon_action = "run_discovery"
            st.rerun()
    with cols[4]:
        if st.button("Export Summary", key="rb_export_discovery", use_container_width=True):
            st.session_state.ribbon_action = "export_discovery"
            st.rerun()
    _ribbon_end()


def render_communication_ribbon() -> None:
    _ribbon_start()
    cols = st.columns([1.0, 1.0, 0.7, 1.1, 0.7], gap="small")
    with cols[0]:
        st.selectbox("Cell Type", ["auto", "leiden", "cell_type"], key="rb_comm_cell_type", label_visibility="visible")
    with cols[1]:
        st.slider("Diffusion Length", 1, 20, 6, key="ctx_comm_k", label_visibility="visible")
    with cols[2]:
        st.number_input("Top N", min_value=3, max_value=30, value=10, key="rb_comm_topn", label_visibility="visible")
    with cols[3]:
        if st.button("Run Analysis", key="rb_run_communication", type="primary", use_container_width=True):
            st.session_state.ribbon_action = "run_communication"
            st.rerun()
    with cols[4]:
        if st.button("Export", key="rb_export_communication", use_container_width=True):
            st.session_state.ribbon_action = "export_communication"
            st.rerun()
    _ribbon_end()


def render_tme_ribbon() -> None:
    _ribbon_start()
    cols = st.columns([1.4, 1.2, 0.8], gap="small")
    with cols[0]:
        st.multiselect("Marker Sets", ["immune", "stromal", "tumor", "caf"], default=["immune", "stromal"], key="rb_tme_markers", label_visibility="visible")
    with cols[1]:
        if st.button("Run TME", key="rb_run_tme", type="primary", use_container_width=True):
            st.session_state.ribbon_action = "run_tme"
            st.rerun()
    with cols[2]:
        if st.button("Export Report", key="rb_export_tme", use_container_width=True):
            st.session_state.ribbon_action = "export_tme"
            st.rerun()
    _ribbon_end()


def render_report_ribbon() -> None:
    _ribbon_start()
    cols = st.columns([1.0, 0.9, 0.9, 1.0, 1.0, 1.0], gap="small")
    with cols[0]:
        st.selectbox("Report Type", ["Full Discovery", "Benchmark Only", "Communication Only"], key="rb_report_type", label_visibility="visible")
    with cols[1]:
        st.checkbox("Include Figures", value=True, key="rb_report_figures", label_visibility="visible")
    with cols[2]:
        st.checkbox("Include Tables", value=True, key="rb_report_tables", label_visibility="visible")
    with cols[3]:
        if st.button("Generate HTML", key="rb_gen_html", type="primary", use_container_width=True):
            st.session_state.ribbon_action = "gen_html"
            st.rerun()
    with cols[4]:
        if st.button("Generate PDF", key="rb_gen_pdf", use_container_width=True):
            st.session_state.ribbon_action = "gen_pdf"
            st.rerun()
    with cols[5]:
        if st.button("Download Bundle", key="rb_gen_bundle", use_container_width=True):
            st.session_state.ribbon_action = "gen_bundle"
            st.rerun()
    _ribbon_end()


def render_context_controls(active_module: str) -> None:
    active_module = resolve_module(active_module)
    mod = get_module(active_module)
    if active_module == "benchmark":
        render_benchmark_ribbon()
    elif active_module == "discovery":
        render_discovery_ribbon()
    elif active_module in ("report_export", "report", "notebook"):
        render_report_ribbon()
        st.caption("Notebook, HTML/PDF export, and data bundle")
    elif active_module == "ai_review":
        st.caption("Grounded Q&A — no external LLM")
    else:
        st.caption(mod.get("description", ""))
