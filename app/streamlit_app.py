"""
MBSI Studio — Physics-Aware Spatial Biology Intelligence
Main dashboard cockpit (opens directly into reference layout).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.components.demo_data import generate_dashboard_demo, CELL_TYPE_COLORS, CELL_COUNTS
from app.components.layout import (
    inject_styles, render_navbar, render_subtabs,
    render_left_sidebar, render_statusbar,
)
from app.components.histology import make_histology_overlay, make_marker_spatial_heatmap, make_ligand_gradient
from app.components.network import neighborhood_graph, interactions_bar
from app.components.tables import render_pathway_table
from app.components.cards import (
    render_metric_strip, donut_composition, pseudotime_scatter,
    causal_ranking, invasion_heatmap, treatment_radar, export_all,
)
from app.components.page_utils import init_session

st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session()
inject_styles()

if "dashboard_demo" not in st.session_state:
    st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)

demo = st.session_state.dashboard_demo
summary = demo["summary"]

render_navbar(active="Analysis")
render_subtabs(active="Spatial Map")

# --- Main grid: 14% | 49% | 20% | 17% ---
left, center, mid_r, far_r = st.columns([1.4, 4.9, 2.0, 1.7], gap="small")

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
    st.caption("MBSI Studio v2.0.0")

with center:
    st.markdown('<div class="mbsi-panel-heading">Histology & Reconstruction Overlay</div>', unsafe_allow_html=True)
    ctrl_cols = st.columns([3, 1])
    with ctrl_cols[1]:
        st.markdown('<div class="mbsi-panel-title">Layer Control</div>', unsafe_allow_html=True)
        show_he = st.toggle("H&E Image", value=True, key="ly_he")
        show_cells = st.toggle("Reconstructed Cells", value=True, key="ly_cells")
        show_types = st.toggle("Cell Type Colors", value=True, key="ly_types")
        show_bound = st.toggle("Boundaries", value=True, key="ly_bound")
        st.toggle("Neighborhood Graph", value=False, key="ly_nhood")
        st.toggle("Ligand Gradients", value=False, key="ly_lig")
        st.toggle("Tissue Mask", value=False, key="ly_mask")
        st.markdown('<div class="mbsi-panel-title" style="margin-top:8px;">Cell Types</div>', unsafe_allow_html=True)
        for ct, color in list(CELL_TYPE_COLORS.items())[:8]:
            cnt = CELL_COUNTS.get(ct, 0)
            st.markdown(
                f'<div class="mbsi-legend-item"><span class="mbsi-legend-dot" style="background:{color};"></span>'
                f'{ct} <span style="color:#9aa7b8;margin-left:auto;">{cnt:,}</span></div>',
                unsafe_allow_html=True,
            )

    with ctrl_cols[0]:
        fig_map = make_histology_overlay(
            demo["histology_image"], demo["cells"],
            tissue_extent=demo["tissue_extent"],
            show_he=show_he, show_cells=show_cells, show_boundaries=show_bound,
            show_types=show_types, boundaries=demo["boundaries"],
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    render_metric_strip(summary)

with mid_r:
    st.markdown('<div class="mbsi-panel"><div class="mbsi-panel-title">Cell Neighborhood</div>', unsafe_allow_html=True)
    radius = st.selectbox("Radius", ["30 µm", "50 µm", "100 µm"], index=0, key="nhood_radius", label_visibility="collapsed")
    st.plotly_chart(
        neighborhood_graph(demo["network_nodes"], demo["network_edges"]),
        use_container_width=True, config={"displayModeBar": False}, key="nhood_fig",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="mbsi-panel"><div class="mbsi-panel-title">Top Interactions (Niche → Target)</div>', unsafe_allow_html=True)
    st.plotly_chart(
        interactions_bar(demo["interactions"]),
        use_container_width=True, config={"displayModeBar": False}, key="inter_fig",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with far_r:
    st.markdown('<div class="mbsi-panel"><div class="mbsi-panel-title">Ligand–Receptor Pathways</div>', unsafe_allow_html=True)
    pathway_filter = st.selectbox(
        "Pathways", ["All Pathways", "CXCL12", "TGFB1", "VEGFA"],
        key="path_filter", label_visibility="collapsed",
    )
    render_pathway_table(demo["pathways"], pathway_filter)
    if st.button("View Pathway Details", use_container_width=True, key="path_details"):
        st.toast("Pathway details loaded (computational hypothesis).")
    st.markdown("</div>", unsafe_allow_html=True)

    ligand = st.selectbox("Ligand Gradient", ["CXCL12", "CCL5", "VEGFA"], key="lig_sel")
    st.plotly_chart(
        make_ligand_gradient(demo["ligand_field"], title=f"Ligand Gradient ({ligand})"),
        use_container_width=True, config={"displayModeBar": False}, key="lig_fig",
    )

# --- Bottom analytics grid (6 cards) ---
st.markdown('<div class="mbsi-panel-title">Multi-Modal Analytics</div>', unsafe_allow_html=True)
b1, b2, b3, b4, b5, b6 = st.columns(6, gap="small")

with b1:
    gene = st.selectbox("Marker", list(demo["marker_maps"].keys()), key="marker_gene")
    st.plotly_chart(
        make_marker_spatial_heatmap(demo["marker_maps"][gene], title=f"Marker Expression ({gene})"),
        use_container_width=True, config={"displayModeBar": False}, key="m1",
    )

with b2:
    st.plotly_chart(
        donut_composition(demo["composition"]),
        use_container_width=True, config={"displayModeBar": False}, key="m2",
    )

with b3:
    traj_type = st.selectbox("Trajectory", ["Tumor Epithelial", "T cells", "CAF (myCAFs)"], key="traj_sel")
    st.plotly_chart(
        pseudotime_scatter(demo["trajectory"], title=f"Pseudotime / Trajectory ({traj_type})"),
        use_container_width=True, config={"displayModeBar": False}, key="m3",
    )

with b4:
    st.plotly_chart(
        causal_ranking(demo["causal"]),
        use_container_width=True, config={"displayModeBar": False}, key="m4",
    )

with b5:
    inv_mode = st.selectbox("Analysis", ["Boundary Leakage", "Invasion Score"], key="inv_mode")
    st.plotly_chart(
        invasion_heatmap(demo["invasion_field"], title="Invasion & Boundary Analysis"),
        use_container_width=True, config={"displayModeBar": False}, key="m5",
    )

with b6:
    tx = st.selectbox("Treatment", list(demo["treatment"].keys()), key="tx_sel")
    st.plotly_chart(
        treatment_radar(demo["treatment"], demo["baseline"], tx),
        use_container_width=True, config={"displayModeBar": False}, key="m6",
    )

# Status bar actions (functional buttons above fixed bar)
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

render_statusbar()
