"""Analysis subtab panels — demo-safe, no backend required."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.components.demo_data import CELL_TYPE_COLORS, CELL_COUNTS
from app.components.histology import make_histology_overlay, make_marker_spatial_heatmap, make_ligand_gradient
from app.components.cards import donut_composition, pseudotime_scatter, causal_ranking, invasion_heatmap
from app.components.network import neighborhood_graph, interactions_bar
from app.components.tables import render_pathway_table
from app.components.safe import safe_plotly


def render_spatial_map_panel(demo: Dict[str, Any]) -> None:
    """Histology & reconstruction overlay (default Analysis view)."""
    st.markdown('<div class="mbsi-panel-heading">Histology & Reconstruction Overlay</div>', unsafe_allow_html=True)
    ctrl_cols = st.columns([3, 1])
    with ctrl_cols[1]:
        st.markdown('<div class="mbsi-panel-title">Layer Control</div>', unsafe_allow_html=True)
        show_he = st.toggle("H&E Image", value=True, key="ly_he")
        show_cells = st.toggle("Reconstructed Cells", value=True, key="ly_cells")
        show_types = st.toggle("Cell Type Colors", value=True, key="ly_types")
        show_bound = st.toggle("Boundaries", value=True, key="ly_bound")
        for ct, color in list(CELL_TYPE_COLORS.items())[:8]:
            cnt = CELL_COUNTS.get(ct, 0)
            st.markdown(
                f'<div class="mbsi-legend-item"><span class="mbsi-legend-dot" style="background:{color};"></span>'
                f'{ct} <span style="color:#9aa7b8;margin-left:auto;">{cnt:,}</span></div>',
                unsafe_allow_html=True,
            )
    with ctrl_cols[0]:
        fig = make_histology_overlay(
            demo["histology_image"], demo["cells"],
            tissue_extent=demo["tissue_extent"],
            show_he=show_he, show_cells=show_cells, show_boundaries=show_bound,
            show_types=show_types, boundaries=demo["boundaries"],
        )
        safe_plotly(fig, message="Spatial map unavailable.")


def render_cell_types_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### Cell Type Composition")
    safe_plotly(donut_composition(demo["composition"]))
    comp = demo["composition"]
    if isinstance(comp, pd.DataFrame) and not comp.empty:
        st.dataframe(comp, use_container_width=True, hide_index=True)
    else:
        rows = [{"cell_type": k, "count": v} for k, v in CELL_COUNTS.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_clusters_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### Spatial Clusters")
    rng = np.random.default_rng(42)
    n = 120
    df = pd.DataFrame({
        "x": rng.uniform(0, 1, n),
        "y": rng.uniform(0, 1, n),
        "cluster": rng.integers(0, 6, n).astype(str),
    })
    fig = px.scatter(df, x="x", y="y", color="cluster", title="Cluster Assignments")
    fig.update_layout(paper_bgcolor="#0d1828", plot_bgcolor="#07111f", font_color="#f4f7fb")
    safe_plotly(fig)


def render_neighborhoods_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### Cell Neighborhood")
    safe_plotly(neighborhood_graph(demo["network_nodes"], demo["network_edges"]))
    st.markdown("### Top Interactions")
    safe_plotly(interactions_bar(demo["interactions"]))


def render_boundaries_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### Boundary & Invasion")
    safe_plotly(invasion_heatmap(demo["invasion_field"], title="Invasion & Boundary Analysis"))


def render_pathways_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### Ligand–Receptor Pathways")
    pathway_filter = st.selectbox("Pathways", ["All Pathways", "CXCL12", "TGFB1", "VEGFA"], key="path_filter_panel")
    render_pathway_table(demo["pathways"], pathway_filter)
    ligand = st.selectbox("Ligand Gradient", ["CXCL12", "CCL5", "VEGFA"], key="lig_sel_panel")
    safe_plotly(make_ligand_gradient(demo["ligand_field"], title=f"Ligand Gradient ({ligand})"))


def render_3d_panel(demo: Dict[str, Any]) -> None:
    st.markdown("### 3D Tissue View")
    cells = demo.get("cells", [])
    if not cells:
        st.info("3D view requires cell coordinates — load spatial data.")
        return
    xs = [c["x"] for c in cells[:400]]
    ys = [c["y"] for c in cells[:400]]
    zs = [c.get("z", 0.0) for c in cells[:400]]
    colors = [CELL_TYPE_COLORS.get(c.get("type", "Other"), "#b8c1cc") for c in cells[:400]]
    fig = go.Figure(data=[go.Scatter3d(x=xs, y=ys, z=zs, mode="markers", marker=dict(size=2, color=colors))])
    fig.update_layout(
        title="3D Cell Cloud", paper_bgcolor="#0d1828", scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
    )
    safe_plotly(fig)
