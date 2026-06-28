"""
MBSI Studio — Physics-Aware Spatial Biology Intelligence
Main dashboard cockpit (opens directly into reference layout).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.components.demo_data import generate_dashboard_demo
from app.components.layout import inject_styles, render_analysis_subtabs, render_left_sidebar
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from app.components.analysis_panels import (
    render_spatial_map_panel,
    render_cell_types_panel,
    render_clusters_panel,
    render_neighborhoods_panel,
    render_boundaries_panel,
    render_pathways_panel,
    render_3d_panel,
)
from app.components.cards import render_metric_strip, export_all
from app.components.page_utils import init_session

PANEL_ROUTER = {
    "Spatial Map": render_spatial_map_panel,
    "Cell Types": render_cell_types_panel,
    "Clusters": render_clusters_panel,
    "Neighborhoods": render_neighborhoods_panel,
    "Boundaries": render_boundaries_panel,
    "Pathways": render_pathways_panel,
    "3D View": render_3d_panel,
}

st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session()
inject_styles()
render_topnav(active="Analysis")

if "dashboard_demo" not in st.session_state:
    st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)

demo = st.session_state.dashboard_demo
summary = demo["summary"]

selected_tab = render_analysis_subtabs()

left, center = st.columns([1.4, 8.6], gap="small")

with left:
    render_left_sidebar(summary)
    if st.button("Run Full Pipeline", type="primary", use_container_width=True, key="run_pipeline"):
        st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
        st.session_state.last_run = "Full pipeline"
        st.toast("Full pipeline completed successfully.")
        st.rerun()
    if st.button("Reset Session", use_container_width=True, key="reset_sess"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    with st.expander("Spatial Analysis", expanded=False):
        st.caption(
            "Analytical outputs are computational results for research use only. "
            "Biological and clinical conclusions require independent validation."
        )
        if st.button("Open Analysis Page", use_container_width=True, key="goto_analysis"):
            st.switch_page("pages/06_Analysis.py")
    st.caption("MBSI Studio v2.0.0")

with center:
    panel_fn = PANEL_ROUTER.get(selected_tab, render_spatial_map_panel)
    panel_fn(demo)
    if selected_tab == "Spatial Map":
        render_metric_strip(summary)

# Quick actions above status bar
sa1, sa2, sa3, _ = st.columns([1, 1, 1, 6])
with sa1:
    if st.button("AI Copilot", key="sb_copilot"):
        st.switch_page("pages/08_AI_Copilot.py")
with sa2:
    if st.button("Quick Report", key="sb_report"):
        st.switch_page("pages/09_Export.py")
with sa3:
    if st.button("Export All", key="sb_export_all"):
        out = export_all(demo)
        st.toast(f"Exported to {out}")

render_statusbar(show_actions=False)
