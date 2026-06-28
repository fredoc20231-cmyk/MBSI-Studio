"""TME workspace."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import demo_banner, add_finding
from mbsi.reports.registry import register_table


def render():
    demo_banner()
    st.markdown("### TME Intelligence")
    if st.button("Run TME Analysis", type="primary"):
        try:
            from mbsi.tme import run_tme_analysis, make_tme_demo_adata
            out = run_tme_analysis(make_tme_demo_adata(seed=42))
            st.session_state.tme_results = out
            st.session_state.last_run = "TME"
            add_finding("TME", f"{len(out.get('summary', []))} niche types")
        except Exception as exc:
            st.warning(f"TME failed: {exc}")
            return
    results = st.session_state.get("tme_results")
    if not results:
        st.info("Run TME analysis to detect niches.")
        return
    summary = results.get("summary")
    if summary is not None and not summary.empty:
        register_table("tme", "niche_summary", summary)
        from mbsi.visualization.tme_plots import plot_niche_summary
        render_interactive_plot(plot_niche_summary(summary), title="TME Niches", module="tme")
