"""Communication workspace."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import demo_banner, add_finding
from mbsi.reports.registry import register_table


def render():
    demo_banner()
    st.markdown("### Communication Intelligence")
    k = st.session_state.get("ctx_comm_k", 6)
    if st.button("Run Communication Analysis", type="primary"):
        try:
            from mbsi.communication import run_communication_analysis, make_communication_demo_adata
            adata = make_communication_demo_adata(seed=42)
            out = run_communication_analysis(adata, k=k)
            st.session_state.communication_results = out
            st.session_state.last_run = "Communication"
            add_finding("Communication", f"Top pathway: {out.get('top_pathway', 'N/A')}")
        except Exception as exc:
            st.warning(f"Communication failed: {exc}")
            return
    results = st.session_state.get("communication_results")
    if not results:
        st.info("Run analysis to score L-R pathways.")
        return
    rankings = results.get("pathway_rankings")
    if rankings is not None and not rankings.empty:
        register_table("communication", "pathway_rankings", rankings)
        from mbsi.visualization.communication_plots import plot_pathway_rankings
        render_interactive_plot(plot_pathway_rankings(rankings), title="Pathways", module="communication")
