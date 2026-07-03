"""Read-only project dashboard summary (not in main nav — use project_setup)."""

from __future__ import annotations

import streamlit as st

from app.components.developer_mode import is_developer_mode
from app.components.page_header import render_page_header
from app.workspaces._helpers import ensure_demo


def render_dashboard_summary() -> None:
    """Compact read-only summary from session metadata."""
    meta = st.session_state.get("project_metadata", {})
    design = st.session_state.get("experimental_design", {})
    plat = st.session_state.get("platform_metadata", {})
    adata = st.session_state.get("adata")
    adata_loaded = adata is not None and not st.session_state.get("using_synthetic_demo", False)
    if adata_loaded:
        data_mode = "Uploaded"
    elif st.session_state.get("using_synthetic_demo") and is_developer_mode():
        data_mode = "Developer demo"
    else:
        data_mode = "Not loaded"

    render_page_header(
        "Project Dashboard",
        "Read-only summary — edit study design in Project Setup & Data Upload.",
        icon="📋",
    )

    if meta.get("project_title"):
        st.markdown(f"**{meta['project_title']}**")
        if meta.get("biological_question"):
            st.write(meta["biological_question"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Study type", design.get("study_type", "—"))
    c2.metric("Samples", design.get("num_samples", "—"))
    c3.metric("Data mode", data_mode)
    c4.metric("Completeness", f"{st.session_state.get('project_completeness', 0)}/100")

    if adata_loaded:
        st.success(f"AnnData in session: {adata.n_obs:,} spots × {adata.n_vars:,} genes")
    else:
        st.info("No spatial data loaded — upload in Study & Data.")

    if plat.get("platforms"):
        st.caption(f"Platforms: {', '.join(plat['platforms'])}")


def render() -> None:
    render_dashboard_summary()
    adata = st.session_state.get("adata")
    from app.components.cards import render_metric_strip

    if adata is not None and not st.session_state.get("using_synthetic_demo", False):
        summary = {
            "cells": int(adata.n_obs),
            "cell_types_n": int(adata.obs["cluster"].nunique()) if "cluster" in adata.obs.columns else 0,
            "resolution_um": st.session_state.get("mbsi_readiness", {}).get("resolution_um", "—"),
            "boundary_leakage": 0.0,
            "morans_i": 0.0,
        }
        render_metric_strip(summary)
    elif is_developer_mode():
        demo = ensure_demo()
        render_metric_strip(demo["summary"])

    if st.button("Open Project Setup & Data Upload", key="proj_go_setup", type="primary"):
        st.session_state.active_module = "project_setup"
        st.rerun()
