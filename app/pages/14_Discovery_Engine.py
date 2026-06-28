"""Biopharma Discovery Engine — flagship dashboard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from app.components.safe import safe_get, safe_plotly
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
            st.session_state.benchmark_results = results.get("benchmark_results")
            st.session_state.communication_results = results.get("communication_results")
            st.session_state.tme_results = results.get("tme_results")
            export_discovery_engine(results, OUTPUT_DIR)
            st.session_state.last_run = "Discovery Engine"
        if results.get("warnings"):
            st.warning("Completed with warnings: " + "; ".join(results["warnings"]))
        else:
            st.success("Discovery pipeline complete.")

    results = st.session_state.get("discovery_results")
    if results:
        st.metric("Status", results.get("status", "unknown"))
        st.metric("Readiness", f"{safe_get(results, 'benchmark_results', 'readiness_score', default=0)}/100")
        st.metric("Top Pathway", safe_get(results, "communication_results", "top_pathway", default="—"))
        for w in results.get("warnings", []):
            st.caption(f"⚠ {w}")

with center:
    st.markdown("**Discovery Map**")
    results = st.session_state.get("discovery_results")
    if not results:
        st.info("Run the discovery pipeline to render spatial maps.")
    else:
        adata = results.get("adata")
        ie = safe_get(results, "tme_results", "niches", "immune_exclusion")
        if adata is not None and ie and "score" in ie:
            coords = adata.obsm.get("spatial")
            if coords is not None:
                safe_plotly(plot_niche_map(coords[:, 0], coords[:, 1], ie["score"], title="Immune Exclusion Map"))
            else:
                st.info("Spatial coordinates unavailable.")
        else:
            st.info("TME niche map unavailable — run pipeline or check warnings.")

with right:
    st.markdown("**Actionable Findings**")
    results = st.session_state.get("discovery_results")
    findings = safe_get(results, "actionable_findings", default=[]) if results else []
    if findings:
        for f in findings:
            st.markdown(f"**{f.get('title', 'Finding')}**")
            st.caption(f"{f.get('detail', '')} [{f.get('priority', 'info')}]")
    else:
        st.caption("Computational hypotheses will appear here.")

results = st.session_state.get("discovery_results")
if results:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        lb = safe_get(results, "benchmark_results", "leaderboard")
        if lb is not None and hasattr(lb, "empty") and not lb.empty:
            safe_plotly(plot_leaderboard_bars(lb))
        else:
            st.info("Benchmark leaderboard unavailable.")
    with c2:
        rankings = safe_get(results, "communication_results", "pathway_rankings")
        if rankings is not None and hasattr(rankings, "empty") and not rankings.empty:
            safe_plotly(plot_pathway_rankings(rankings))
        else:
            st.info("Communication pathways unavailable.")
    with c3:
        summary = safe_get(results, "tme_results", "summary")
        if summary is not None and hasattr(summary, "empty") and not summary.empty:
            safe_plotly(plot_niche_summary(summary))
        else:
            st.info("TME summary unavailable.")

    if st.button("Export Biopharma Report"):
        path = generate_spatial_biomarker_report(
            results.get("benchmark_results"),
            results.get("communication_results"),
            results.get("tme_results"),
            OUTPUT_DIR,
        )
        st.success(f"Report: {path}")
        if path.exists():
            st.download_button("Download Report HTML", path.read_text(), file_name="biopharma_discovery_report.html")

render_statusbar(show_actions=False)
