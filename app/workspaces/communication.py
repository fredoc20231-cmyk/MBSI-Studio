"""Communication workspace."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import add_finding, demo_banner, safe_register_finding, safe_register_table


def _run_communication() -> None:
    k = int(st.session_state.get("ctx_comm_k", 6))
    try:
        from mbsi.communication import make_communication_demo_adata, run_communication_analysis
        adata = make_communication_demo_adata(seed=42)
        out = run_communication_analysis(adata, k=k)
        st.session_state.communication_results = out
        st.session_state.last_run = "Communication"
        top = out.get("top_pathway", "N/A")
        add_finding("Communication", f"Top pathway: {top}", module="communication")
        safe_register_finding(f"Top pathway: {top}", section="communication", module="communication", title="Top pathway")
    except Exception as exc:
        st.warning(f"Communication failed: {exc}")


def render():
    demo_banner()
    action = st.session_state.pop("ribbon_action", None)
    if action == "run_communication":
        _run_communication()
    elif action == "export_communication":
        st.toast("Communication outputs queued for report.")

    st.markdown("### Communication Intelligence")
    if st.button("Run Communication Analysis", type="primary", key="ws_run_comm"):
        _run_communication()

    results = st.session_state.get("communication_results")
    if not results:
        st.info("Run analysis to score L-R pathways.")
        return
    rankings = results.get("pathway_rankings")
    if rankings is not None and not rankings.empty:
        safe_register_table("communication", "pathway_rankings", rankings)
        st.dataframe(rankings.head(int(st.session_state.get("rb_comm_topn", 10))), use_container_width=True, hide_index=True)
        from mbsi.visualization.communication_plots import plot_pathway_rankings
        render_interactive_plot(plot_pathway_rankings(rankings), title="Pathways", module="communication", key="comm_pathways")
