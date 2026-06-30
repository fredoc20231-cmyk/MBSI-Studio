"""Reconstruction workspace."""

import streamlit as st
from app.components.page_utils import ensure_adata, ensure_reconstructed, has_real_adata
from app.workspaces._helpers import demo_banner, add_finding


def render():
    demo_banner()
    st.markdown("### MBSI Reconstruction")
    if not has_real_adata() and not st.session_state.get("using_synthetic_demo"):
        st.info("Upload real spatial data in Study & Data to run reconstruction.")
        return
    if st.button("Run MBSI (quick)", type="primary"):
        try:
            if not ensure_adata(show_warning=True):
                return
            if not ensure_reconstructed(show_warning=True, quick=True):
                return
            st.session_state.last_run = "MBSI reconstruction"
            add_finding("Reconstruction", "MBSI run completed")
            st.success("Reconstruction ready.")
        except Exception as exc:
            st.warning(f"Reconstruction failed: {exc}")
