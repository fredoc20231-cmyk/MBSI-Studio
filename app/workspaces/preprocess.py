"""Preprocess workspace."""

import streamlit as st
from app.components.page_utils import ensure_adata
from app.workspaces._helpers import demo_banner


def render():
    demo_banner()
    ensure_adata(show_warning=False)
    st.markdown("### Preprocess")
    st.slider("Min counts", 0, 500, 10, key="ws_pre_min_counts")
    st.slider("Max mito %", 0, 100, 20, key="ws_pre_max_mito")
    if st.button("Run QC (demo)", type="primary"):
        st.session_state.last_run = "Preprocess QC"
        st.toast("QC complete (demo).")
