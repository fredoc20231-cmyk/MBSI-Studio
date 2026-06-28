"""Project workspace."""

import streamlit as st
from app.workspaces._helpers import ensure_demo, demo_banner
from app.components.cards import render_metric_strip


def render():
    demo_banner()
    demo = ensure_demo()
    st.markdown("### Project Overview")
    render_metric_strip(demo["summary"])
    st.info("Load data in Upload or run Discovery for full pipeline outputs.")
