import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.components.layout import inject_styles, metric_tile
from app.components.page_utils import init_session, guardrail_banner, ensure_reconstructed, save_metrics
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.validation import run_validation_suite

st.set_page_config(page_title="Validation | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_reconstructed(quick=True, show_warning=False)

render_topnav(active="Validation")

st.markdown("### Validation & Benchmarking")

if st.button("Run Validation", type="primary"):
    true = st.session_state.true_adata or st.session_state.ground_truth
    if true is None:
        st.warning("No ground truth — using spot-level self-comparison.")
        true = st.session_state.adata
    st.session_state.metrics = run_validation_suite(
        true, st.session_state.reconstructed, st.session_state.adata
    )
    st.session_state.analysis_state["metrics"] = st.session_state.metrics
    save_metrics()
    st.session_state.last_run = "Validation"
    st.success("Validation complete.")

if st.session_state.metrics:
    numeric = {k: v for k, v in st.session_state.metrics.items() if isinstance(v, (int, float))}
    cols = st.columns(min(4, len(numeric)) or 1)
    for col, (k, v) in zip(cols, list(numeric.items())[:4]):
        with col:
            metric_tile(k.replace("_", " ").title(), f"{v:.4f}" if isinstance(v, float) else str(v))
    if numeric:
        st.bar_chart(numeric)

render_statusbar(show_actions=False)
