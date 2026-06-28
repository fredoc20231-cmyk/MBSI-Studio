"""Spatial analysis workspace."""

import streamlit as st
from app.components.analysis_panels import render_spatial_map_panel, render_cell_types_panel
from app.components.layout import render_analysis_subtabs
from app.workspaces._helpers import ensure_demo, demo_banner


def render():
    demo_banner()
    demo = ensure_demo()
    st.markdown("### Spatial Analysis")
    tab = render_analysis_subtabs()
    if tab == "Cell Types":
        render_cell_types_panel(demo)
    else:
        render_spatial_map_panel(demo)
