"""Export — full results report matching dashboard aesthetic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import streamlit as st

from app.components.layout import inject_styles, render_navbar, render_statusbar
from app.components.demo_data import generate_dashboard_demo
from app.components.page_utils import init_session
from app.components.cards import (
    render_metric_strip, export_all, donut_composition, causal_ranking,
    treatment_radar, invasion_heatmap,
)
from app.components.histology import make_histology_overlay, make_ligand_gradient
from app.components.network import neighborhood_graph, interactions_bar

st.set_page_config(page_title="Export | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")
init_session()
inject_styles()
render_navbar(active="Export")

if "dashboard_demo" not in st.session_state:
    st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
demo = st.session_state.dashboard_demo

st.markdown(
    """
    <div class="mbsi-panel" style="padding:16px;margin-bottom:12px;">
      <h2 style="margin:0;color:#f4f7fb;">MBSI Studio — Full Analysis Report</h2>
      <p style="color:#9aa7b8;margin:8px 0 0;">
        Reconstruction estimate | Computational hypothesis | Requires experimental validation
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

render_metric_strip(demo["summary"])

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(
        make_histology_overlay(demo["histology_image"], demo["cells"],
                               tissue_extent=demo["tissue_extent"], boundaries=demo["boundaries"]),
        use_container_width=True, config={"displayModeBar": False},
    )
with c2:
    st.plotly_chart(neighborhood_graph(demo["network_nodes"], demo["network_edges"]),
                    use_container_width=True, config={"displayModeBar": False})

g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(donut_composition(demo["composition"]), use_container_width=True, config={"displayModeBar": False})
with g2:
    st.plotly_chart(causal_ranking(demo["causal"]), use_container_width=True, config={"displayModeBar": False})
with g3:
    st.plotly_chart(treatment_radar(demo["treatment"], demo["baseline"], "Cisplatin"),
                    use_container_width=True, config={"displayModeBar": False})

st.markdown("---")
e1, e2, e3, e4 = st.columns(4)
with e1:
    if st.button("Export All (CSV + JSON)", type="primary", use_container_width=True):
        out = export_all(demo)
        st.success(f"Saved to {out}")
with e2:
    if st.button("Export HTML Report", use_container_width=True):
        out = Path("data/outputs/report.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"<html><body><h1>MBSI Report</h1><pre>{json.dumps(demo['summary'], indent=2)}</pre></body></html>")
        st.success(f"Saved {out}")
with e3:
    st.download_button("Download Summary JSON", json.dumps(demo["summary"], indent=2),
                       file_name="summary.json", use_container_width=True)
with e4:
    st.download_button("Download Pathways CSV", demo["pathways"].to_csv(index=False),
                       file_name="pathways.csv", use_container_width=True)

render_statusbar()
