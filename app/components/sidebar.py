"""Left sidebar controls for analysis cockpit."""

import streamlit as st

from app.components.layout import metric_tile


MODALITIES = [
    ("Visium spots", "adata"),
    ("H&E histology", "spatial_demo"),
    ("Cell reconstruction", "reconstructed"),
    ("Neighborhood graph", "spatial_demo"),
    ("L-R signaling", "spatial_demo"),
    ("Boundary intelligence", "spatial_demo"),
    ("Causal model", "spatial_demo"),
    ("Digital twin", "spatial_demo"),
]


def _readiness_score() -> float:
    score = 0.0
    if st.session_state.get("adata") is not None:
        score += 0.25
    if st.session_state.get("reconstructed") is not None:
        score += 0.25
    if st.session_state.get("spatial_demo"):
        score += 0.35
    if st.session_state.get("metrics"):
        score += 0.15
    return min(1.0, score)


def render_analysis_sidebar() -> None:
    """Project panel, data summary, modalities, readiness, pipeline controls."""
    with st.sidebar:
        st.markdown("### Project")
        project = st.text_input("Project name", value=st.session_state.get("project_name", "Advanced Spatial Demo"))
        st.session_state.project_name = project

        demo = st.session_state.get("spatial_demo") or {}
        n_cells = demo.get("n_cells_total", 0)
        n_spots = demo.get("n_spots", 0)
        if st.session_state.adata is not None:
            n_spots = st.session_state.adata.n_obs

        st.markdown("---")
        st.markdown("**Data Summary**")
        c1, c2 = st.columns(2)
        c1.metric("Cells", f"{n_cells:,}" if n_cells else "—")
        c2.metric("Spots", f"{n_spots:,}" if n_spots else "—")

        st.markdown("---")
        st.markdown("**Modalities**")
        for label, key in MODALITIES:
            ready = bool(st.session_state.get(key) or (key == "spatial_demo" and demo))
            st.checkbox(label, value=ready, disabled=True, key=f"mod_{label}")

        readiness = _readiness_score()
        st.markdown("**Pipeline Readiness**")
        st.progress(readiness)
        st.caption(f"{readiness * 100:.0f}% ready")

        st.markdown("---")
        if st.button("Run Full Pipeline", type="primary", use_container_width=True):
            _run_full_pipeline()
        if st.button("Reset Session", use_container_width=True):
            _reset_session()
            st.rerun()


def _run_full_pipeline() -> None:
    from app.components.page_utils import ensure_advanced_demo, run_local_pipeline

    ensure_advanced_demo()
    with st.spinner("Running full MBSI pipeline..."):
        run_local_pipeline(quick=True)
    st.success("Pipeline complete.")
    st.session_state.last_run = "Full pipeline"


def _reset_session() -> None:
    from app.components.page_utils import init_session, load_advanced_demo_into_session

    keys_to_clear = list(st.session_state.keys())
    for k in keys_to_clear:
        del st.session_state[k]
    init_session()
    load_advanced_demo_into_session()
