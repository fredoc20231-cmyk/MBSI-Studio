"""Reconstruction workspace."""

import streamlit as st
from app.components.page_utils import ensure_adata, ensure_reconstructed
from app.workspaces._helpers import demo_banner, add_finding


def render():
    demo_banner()
    st.markdown("### MBSI Reconstruction")
    if st.button("Run MBSI (quick)", type="primary"):
        try:
            ensure_adata(show_warning=False)
            ensure_reconstructed(show_warning=False, quick=True)
            st.session_state.last_run = "MBSI reconstruction"
            add_finding("Reconstruction", "MBSI run completed")
            st.success("Reconstruction ready.")
        except Exception as exc:
            st.warning(f"Reconstruction failed: {exc}")
