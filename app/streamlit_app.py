"""MBSI Studio Streamlit entry point with browser-visible fallback."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from app.components.layout import inject_styles
    from app.components.saas_shell import render_saas_app
    from app.components.theme import init_theme_state

    init_theme_state()
    inject_styles()
    render_saas_app()
except Exception as exc:
    st.title("MBSI Studio — Safe Launch Mode")
    st.error("The main app shell failed, but Streamlit is running.")
    st.write(str(exc))
    st.info("Run the launch import smoke test, then restart Streamlit.")
