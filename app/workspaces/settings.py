"""Settings workspace."""

import streamlit as st
from app.components.page_header import render_page_header
from app.components.theme import render_theme_settings


def render():
    render_page_header(
        "Settings",
        "Theme, drawer, and workspace preferences.",
        icon="⚙️",
    )
    render_theme_settings()
    st.divider()
    st.toggle("Show results drawer", value=st.session_state.get("saas_drawer_open", True), key="saas_drawer_open")
    st.caption("Theme and platform defaults are also available from the header Settings panel.")
    st.caption("Legacy multipage routes remain under app/pages/ for compatibility.")
