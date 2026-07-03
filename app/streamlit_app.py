"""MBSI Studio Streamlit entry point with browser-visible fallback."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _dashboard_mode_enabled() -> bool:
    env_flag = os.environ.get("MBSI_DASHBOARD", "").lower() in ("1", "true", "yes")
    query_flag = st.query_params.get("dashboard") in ("1", "true", "yes")
    session_flag = bool(st.session_state.get("mbsi_dashboard_mode"))
    return env_flag or query_flag or session_flag


try:
    from app.components.layout import inject_styles
    from app.components.theme import init_theme_state

    init_theme_state()
    inject_styles()

    if _dashboard_mode_enabled():
        st.markdown('<div class="mbsi-app">', unsafe_allow_html=True)
        from app.components.dashboard_cockpit import render_dashboard_cockpit

        render_dashboard_cockpit(show_navbar=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        from app.components.saas_shell import render_saas_app

        render_saas_app()
except Exception as exc:
    st.title("MBSI Studio — Safe Launch Mode")
    st.error("The main app shell failed, but Streamlit is running.")
    st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), language="python")
    st.info("Run: python scripts/smoke_test_launch_imports.py, then restart Streamlit.")
