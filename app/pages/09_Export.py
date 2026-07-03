"""Export — real session results (developer dashboard report optional)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import streamlit as st

from app.components.developer_mode import is_developer_mode, production_mode_message
from app.components.layout import inject_styles
from app.components.page_utils import init_session, has_real_adata
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar

st.set_page_config(page_title="Export | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")
init_session()
inject_styles()
render_topnav(active="Export")

if not is_developer_mode():
    st.markdown("### Report & Export")
    st.info(production_mode_message())
    if has_real_adata():
        adata = st.session_state.adata
        st.success(f"Real data loaded: {adata.n_obs:,} observations × {adata.n_vars:,} genes")
        analysis = st.session_state.get("analysis_results")
        if analysis:
            st.json({"status": analysis.get("status"), "platform": analysis.get("platform")})
        st.caption("Use **Report & Export** in the main SaaS shell for HTML/PDF/bundle generation.")
    else:
        st.warning("No uploaded data — complete Study & Data ingest first.")
    render_statusbar(show_actions=False)
    st.stop()

from app.components.demo_data import generate_dashboard_demo
from app.components.cards import (
    render_metric_strip,
    export_all,
    donut_composition,
    causal_ranking,
    treatment_radar,
    invasion_heatmap,
)
from app.components.histology import make_histology_overlay, make_ligand_gradient
from app.components.network import neighborhood_graph, interactions_bar

if "dashboard_demo" not in st.session_state:
    st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
demo = st.session_state.dashboard_demo

st.markdown(
    """
    <div class="mbsi-panel" style="padding:16px;margin-bottom:12px;">
      <h2 style="margin:0;color:#f4f7fb;">MBSI Studio — Developer Report Preview</h2>
      <p style="color:#9aa7b8;margin:8px 0 0;">
        DEVELOPER_MODE=true — synthetic dashboard for UI QA only
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

render_metric_strip(demo["summary"])

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        make_histology_overlay(
            demo["histology_image"],
            demo["cells"],
            tissue_extent=demo["tissue_extent"],
            boundaries=demo["boundaries"],
        ),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with c2:
    st.plotly_chart(
        neighborhood_graph(demo["network_nodes"], demo["network_edges"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )

g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(donut_composition(demo["composition"]), use_container_width=True, config={"displayModeBar": False})
with g2:
    st.plotly_chart(causal_ranking(demo["causal"]), use_container_width=True, config={"displayModeBar": False})
with g3:
    st.plotly_chart(
        treatment_radar(demo["treatment"], demo["baseline"], "Cisplatin"),
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.plotly_chart(invasion_heatmap(demo["invasion_field"]), use_container_width=True, config={"displayModeBar": False})
st.plotly_chart(make_ligand_gradient(demo["ligand_field"]), use_container_width=True, config={"displayModeBar": False})
st.plotly_chart(interactions_bar(demo["interactions"]), use_container_width=True, config={"displayModeBar": False})

if st.button("Export All (developer)", type="primary"):
    out = export_all(demo, analysis_results=st.session_state.get("analysis_results"))
    st.success(f"Exported to {out}")

render_statusbar(show_actions=False)
