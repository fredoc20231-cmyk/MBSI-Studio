"""
MBSI Studio — SaaS shell entry point.
Legacy multipage routes remain under app/pages/ for compatibility.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.saas_shell import render_saas_app
from app.components.theme import init_theme_state

st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_theme_state()
inject_styles()
render_saas_app()
