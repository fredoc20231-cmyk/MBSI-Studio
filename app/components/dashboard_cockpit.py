"""
Reference dashboard cockpit — histology overlay, analytics cards, export actions.

Used by streamlit_app (dashboard mode) and Report & Export workspace.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.cards import (
    causal_ranking,
    donut_composition,
    export_all,
    invasion_heatmap,
    pseudotime_scatter,
    render_metric_strip,
    treatment_radar,
)
from app.components.demo_data import CELL_COUNTS, CELL_TYPE_COLORS, generate_dashboard_demo
from app.components.histology import make_histology_overlay, make_ligand_gradient, make_marker_spatial_heatmap
from app.components.layout import (
    render_analysis_subtabs,
    render_left_sidebar,
    render_map_toolbar,
    render_navbar,
    render_statusbar,
)
from app.components.network import interactions_bar, neighborhood_graph
from app.components.page_utils import init_session
from app.components.tables import render_pathway_table


def _ensure_demo() -> dict:
    if "dashboard_demo" not in st.session_state:
        st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
    return st.session_state.dashboard_demo


def render_dashboard_cockpit(*, show_navbar: bool = True, compact: bool = False) -> None:
    """Render the full reference dashboard layout."""
    init_session()
    demo = _ensure_demo()
    summary = demo["summary"]

    if show_navbar:
        active = st.session_state.get("mbsi_nav_active", "Analysis")
        render_navbar(active=active)
    render_analysis_subtabs()

    left, center, mid_r, far_r = st.columns([1.4, 4.9, 2.0, 1.7], gap="small")

    with left:
        render_left_sidebar(summary)
        if st.button("Run Full Pipeline", type="primary", use_container_width=True, key="dash_run_pipeline"):
            st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
            st.session_state.last_run = "Full pipeline"
            st.toast("Full pipeline completed successfully.")
            st.rerun()
        if st.button("Reset Session", use_container_width=True, key="dash_reset_sess"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        if not compact:
            with st.expander("Spatial Analysis", expanded=False):
                st.caption(
                    "Analytical outputs are computational results for research use only. "
                    "Biological and clinical conclusions require independent validation."
                )
                if st.button("Open Analysis Page", use_container_width=True, key="dash_goto_analysis"):
                    st.switch_page("pages/06_Analysis.py")
                if st.button("Run Full Analysis (demo)", use_container_width=True, key="dash_run_spatial"):
                    from mbsi.analysis.demo import make_synthetic_visium_adata
                    from mbsi.analysis.pipeline import export_analysis_results, run_standard_spatial_analysis

                    adata = st.session_state.get("adata") or make_synthetic_visium_adata(seed=42)
                    results = run_standard_spatial_analysis(
                        adata,
                        min_counts=0,
                        min_genes=0,
                        max_mito=100.0,
                        n_top_genes=80,
                        n_comps=10,
                        n_neighbors=15,
                        n_pcs=5,
                        spatial_stats_top_n=50,
                    )
                    st.session_state.analysis_results = results
                    st.session_state.adata = results["adata"]
                    st.session_state.marker_table = results["markers"]
                    st.session_state.spatial_stats = results["spatial_stats"]
                    export_analysis_results(results, out_dir=Path("data/outputs"))
                    st.session_state.last_run = "Full spatial analysis"
                    st.toast("Spatial analysis complete.")
        st.caption("MBSI Studio — Results Cockpit")

    with center:
        st.markdown(
            '<div class="mbsi-panel-heading mbsi-histology-card-title">Histology & Reconstruction Overlay</div>',
            unsafe_allow_html=True,
        )
        render_map_toolbar()
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
            st.markdown('<div class="mbsi-histology-card">', unsafe_allow_html=True)
            fig_map = make_histology_overlay(
                demo["histology_image"],
                demo["cells"],
                tissue_extent=demo["tissue_extent"],
                show_he=show_he,
                show_cells=show_cells,
                show_boundaries=show_bound,
                show_types=show_types,
                boundaries=demo["boundaries"],
            )
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        render_metric_strip(summary)

    with mid_r:
        st.markdown('<div class="mbsi-panel"><div class="mbsi-panel-title">Cell Neighborhood</div>', unsafe_allow_html=True)
        st.selectbox("Radius", ["30 µm", "50 µm", "100 µm"], index=0, key="nhood_radius", label_visibility="collapsed")
        st.plotly_chart(
            neighborhood_graph(demo["network_nodes"], demo["network_edges"]),
            use_container_width=True,
            config={"displayModeBar": False},
            key="nhood_fig",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="mbsi-panel"><div class="mbsi-panel-title">Top Interactions (Niche → Target)</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            interactions_bar(demo["interactions"]),
            use_container_width=True,
            config={"displayModeBar": False},
            key="inter_fig",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with far_r:
        st.markdown(
            '<div class="mbsi-panel"><div class="mbsi-panel-title">Ligand–Receptor Pathways</div>',
            unsafe_allow_html=True,
        )
        pathway_filter = st.selectbox(
            "Pathways",
            ["All Pathways", "CXCL12", "TGFB1", "VEGFA"],
            key="path_filter",
            label_visibility="collapsed",
        )
        render_pathway_table(demo["pathways"], pathway_filter)
        if st.button("View Pathway Details", use_container_width=True, key="path_details"):
            st.toast("Pathway details loaded (computational hypothesis).")
        st.markdown("</div>", unsafe_allow_html=True)

        ligand = st.selectbox("Ligand Gradient", ["CXCL12", "CCL5", "VEGFA"], key="lig_sel")
        st.plotly_chart(
            make_ligand_gradient(demo["ligand_field"], title=f"Ligand Gradient ({ligand})"),
            use_container_width=True,
            config={"displayModeBar": False},
            key="lig_fig",
        )

    st.markdown('<div class="mbsi-panel-title">Multi-Modal Analytics</div>', unsafe_allow_html=True)
    b1, b2, b3, b4, b5, b6 = st.columns(6, gap="small")

    with b1:
        gene = st.selectbox("Marker", list(demo["marker_maps"].keys()), key="marker_gene")
        st.plotly_chart(
            make_marker_spatial_heatmap(demo["marker_maps"][gene], title=f"Marker Expression ({gene})"),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m1",
        )

    with b2:
        st.plotly_chart(
            donut_composition(demo["composition"]),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m2",
        )

    with b3:
        traj_type = st.selectbox("Trajectory", ["Tumor Epithelial", "T cells", "CAF (myCAFs)"], key="traj_sel")
        st.plotly_chart(
            pseudotime_scatter(demo["trajectory"], title=f"Pseudotime / Trajectory ({traj_type})"),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m3",
        )

    with b4:
        st.plotly_chart(
            causal_ranking(demo["causal"]),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m4",
        )

    with b5:
        st.selectbox("Analysis", ["Boundary Leakage", "Invasion Score"], key="inv_mode")
        st.plotly_chart(
            invasion_heatmap(demo["invasion_field"], title="Invasion & Boundary Analysis"),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m5",
        )

    with b6:
        tx = st.selectbox("Treatment", list(demo["treatment"].keys()), key="tx_sel")
        st.plotly_chart(
            treatment_radar(demo["treatment"], demo["baseline"], tx),
            use_container_width=True,
            config={"displayModeBar": False},
            key="m6",
        )

    sa1, sa2, sa3, _ = st.columns([1, 1, 1, 6])
    with sa1:
        if st.button("AI Copilot", key="sb_copilot"):
            st.switch_page("pages/08_AI_Copilot.py")
    with sa2:
        if st.button("Quick Report", key="sb_report"):
            st.session_state.mbsi_dashboard_mode = False
            st.session_state.active_module = "report_export"
            if "dashboard" in st.query_params:
                del st.query_params["dashboard"]
            st.rerun()
    with sa3:
        if st.button("Export All", key="sb_export_all"):
            out = export_all(demo, analysis_results=st.session_state.get("analysis_results"))
            st.toast(f"Exported to {out}")

    if show_navbar:
        render_statusbar()
