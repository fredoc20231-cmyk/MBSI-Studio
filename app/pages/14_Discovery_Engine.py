"""Biopharma Discovery Engine — flagship dashboard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.discovery import run_discovery_engine, export_discovery_engine
from mbsi.reports import BIOMARKER_DISCLAIMER, generate_spatial_biomarker_report
from mbsi.visualization.benchmark_plots import plot_leaderboard_bars, plot_readiness_gauge
from mbsi.visualization.tme_plots import plot_niche_map, plot_niche_summary
from mbsi.visualization.communication_plots import plot_pathway_rankings

st.set_page_config(page_title="Discovery Engine | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")
init_session()
inject_styles()
render_topnav(active="Discovery")

st.markdown("## Biopharma Discovery Engine v1")
st.caption(BIOMARKER_DISCLAIMER)

left, center, right = st.columns([1, 2.2, 1])

with left:
    st.markdown("**Engine Status**")
    if st.button("Run Full Discovery Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running benchmark + communication + TME..."):
            results = run_discovery_engine(seed=42)
            st.session_state.discovery_results = results
            st.session_state.benchmark_results = results["benchmark_results"]
            st.session_state.communication_results = results["communication_results"]
            st.session_state.tme_results = results["tme_results"]
            export_discovery_engine(results, OUTPUT_DIR)
            st.session_state.last_run = "Discovery Engine"
        st.success("Discovery pipeline complete.")

    if st.session_state.get("discovery_results"):
        r = st.session_state.discovery_results
        st.metric("Readiness", f"{r['benchmark_results'].get('readiness_score', 0)}/100")
        st.metric("Top Pathway", r["communication_results"].get("top_pathway", "—"))

with center:
    st.markdown("**Discovery Map**")
    results = st.session_state.get("discovery_results")
    if results:
        adata = results["adata"]
        coords = adata.obsm["spatial"]
        ie = results["tme_results"]["niches"]["immune_exclusion"]
        st.plotly_chart(
            plot_niche_map(coords[:, 0], coords[:, 1], ie["score"], title="Immune Exclusion Map"),
            use_container_width=True, config={"displayModeBar": False},
        )
    else:
        st.info("Run the discovery pipeline to render spatial maps.")

with right:
    st.markdown("**Actionable Findings**")
    results = st.session_state.get("discovery_results")
    if results:
        for f in results.get("actionable_findings", []):
            st.markdown(f"**{f['title']}**")
            st.caption(f"{f['detail']} [{f['priority']}]")
    else:
        st.caption("Computational hypotheses will appear here.")

if results := st.session_state.get("discovery_results"):
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        lb = results["benchmark_results"].get("leaderboard")
        if lb is not None and not lb.empty:
            st.plotly_chart(plot_leaderboard_bars(lb), use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(plot_pathway_rankings(results["communication_results"]["pathway_rankings"]), use_container_width=True, config={"displayModeBar": False})
    with c3:
        st.plotly_chart(plot_niche_summary(results["tme_results"]["summary"]), use_container_width=True, config={"displayModeBar": False})

    if st.button("Export Biopharma Report"):
        path = generate_spatial_biomarker_report(
            results["benchmark_results"], results["communication_results"], results["tme_results"], OUTPUT_DIR
        )
        st.success(f"Report: {path}")
        st.download_button("Download Report HTML", path.read_text(), file_name="biopharma_discovery_report.html")

render_statusbar(show_actions=False)
