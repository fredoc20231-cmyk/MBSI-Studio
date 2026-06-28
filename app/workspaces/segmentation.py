"""Segmentation workspace."""

import streamlit as st
from app.workspaces._helpers import ensure_demo, demo_banner


def render():
    demo_banner()
    ensure_demo()
    st.markdown("### Segmentation")
    st.info("Segmentation uses demo histology boundaries. Open legacy page for full controls.")
