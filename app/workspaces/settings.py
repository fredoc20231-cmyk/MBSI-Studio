"""Settings workspace."""

import streamlit as st
from app.components.page_header import render_page_header
from app.components.theme import render_theme_settings
from app.workspaces._helpers import demo_banner


def render():
    demo_banner()
    render_page_header(
        "Settings",
        "Theme, drawer, and workspace preferences.",
        icon="⚙️",
    )
    render_theme_settings()
    st.divider()
    st.toggle("Show results drawer", value=st.session_state.get("saas_drawer_open", True), key="saas_drawer_open")
    st.toggle("Demo mode banner", value=True, disabled=True)
    st.caption("Legacy multipage routes remain under app/pages/ for compatibility.")
