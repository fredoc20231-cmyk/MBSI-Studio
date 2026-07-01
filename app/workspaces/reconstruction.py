"""Reconstruction workspace."""

import streamlit as st
from app.components.notification_center import push_notification
from app.components.page_header import render_page_header
from app.components.page_utils import ensure_adata, ensure_reconstructed, has_real_adata
from app.workspaces._helpers import add_finding


def render():
    render_page_header(
        "Reconstruction",
        "Reconstruct cell-level expression from spatial spot measurements.",
        icon="🔄",
    )
    if not has_real_adata():
        st.info("Upload spatial data in Study Setup & Data to run reconstruction.")
        return
    if st.button("Run MBSI (quick)", type="primary"):
        try:
            if not ensure_adata(show_warning=True):
                return
            if not ensure_reconstructed(show_warning=True, quick=True):
                return
            st.session_state.last_run = "MBSI reconstruction"
            add_finding("Reconstruction", "MBSI run completed")
            push_notification(
                "MBSI reconstruction completed.",
                title="Workflow complete",
                level="success",
                source="reconstruction",
            )
            st.success("Reconstruction ready.")
        except Exception as exc:
            push_notification(str(exc), title="Reconstruction failed", level="error", source="reconstruction")
            st.warning(f"Reconstruction failed: {exc}")
