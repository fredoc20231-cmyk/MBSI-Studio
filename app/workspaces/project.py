"""Read-only project dashboard summary (not in main nav — use project_setup)."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import ensure_demo


def render_dashboard_summary() -> None:
    """Compact read-only summary from session metadata."""
    meta = st.session_state.get("project_metadata", {})
    design = st.session_state.get("experimental_design", {})
    plat = st.session_state.get("platform_metadata", {})
    adata = st.session_state.get("adata")
    using_demo = st.session_state.get("using_synthetic_demo", True)

    st.markdown("### Project Dashboard")
    st.caption("Read-only summary — edit study design in **Project Setup & Data Upload**.")

    if meta.get("project_title"):
        st.markdown(f"**{meta['project_title']}**")
        if meta.get("biological_question"):
            st.write(meta["biological_question"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Study type", design.get("study_type", "—"))
    c2.metric("Samples", design.get("num_samples", "—"))
    c3.metric("Data mode", "Demo" if using_demo else "Uploaded")
    c4.metric("Completeness", f"{st.session_state.get('project_completeness', 0)}/100")

    if adata is not None:
        st.success(f"AnnData in session: {adata.n_obs:,} spots × {adata.n_vars:,} genes")
    else:
        st.info("No spatial data loaded.")

    if plat.get("platforms"):
        st.caption(f"Platforms: {', '.join(plat['platforms'])}")


def render() -> None:
    render_dashboard_summary()
    demo = ensure_demo()
    from app.components.cards import render_metric_strip

    render_metric_strip(demo["summary"])
    if st.button("Open Project Setup & Data Upload", key="proj_go_setup", type="primary"):
        st.session_state.active_module = "project_setup"
        st.rerun()
