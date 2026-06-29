"""Project workspace."""

import streamlit as st
from app.workspaces._helpers import ensure_demo


def render():
    st.markdown("### Project Overview")
    using_demo = st.session_state.get("using_synthetic_demo", True)
    adata = st.session_state.get("adata")
    analysis = st.session_state.get("analysis_results")

    if adata is not None and not using_demo:
        st.success(f"Real data loaded: {adata.n_obs:,} spots × {adata.n_vars:,} genes")
    elif adata is not None:
        st.warning("Synthetic demo data in session — upload real data in Upload workspace.")
    else:
        st.info("No AnnData in session — upload data or load demo.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Data mode", "Demo" if using_demo else "Uploaded")
    c2.metric("Analysis", "Complete" if analysis else "Not run")
    c3.metric("Last run", st.session_state.get("last_run", "—"))

    demo = ensure_demo()
    from app.components.cards import render_metric_strip
    render_metric_strip(demo["summary"])

    st.markdown("**Quick navigation**")
    nav_cols = st.columns(4)
    routes = [
        ("upload", "Upload Data"),
        ("spatial_analysis", "Spatial Analysis"),
        ("discovery", "Discovery"),
        ("report", "Report & Export"),
    ]
    for col, (module_key, label) in zip(nav_cols, routes):
        with col:
            if st.button(label, key=f"proj_nav_{module_key}", use_container_width=True):
                st.session_state.active_module = module_key
                st.rerun()
