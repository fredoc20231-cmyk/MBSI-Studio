"""Discovery workspace."""

import streamlit as st
from app.components.safe import safe_get
from app.components.interactive_figures import render_interactive_plot
from app.components.page_utils import OUTPUT_DIR
from app.workspaces._helpers import demo_banner, add_finding
from mbsi.discovery import run_discovery_engine, export_discovery_engine


def render():
    demo_banner()
    st.markdown("### Biopharma Discovery Engine")
    seed = int(st.session_state.get("ctx_discovery_seed", 42))
    if st.button("Run Discovery Pipeline", type="primary"):
        try:
            out = run_discovery_engine(seed=seed)
            st.session_state.discovery_results = out
            st.session_state.benchmark_results = out.get("benchmark_results")
            st.session_state.communication_results = out.get("communication_results")
            st.session_state.tme_results = out.get("tme_results")
            export_discovery_engine(out, OUTPUT_DIR)
            st.session_state.last_run = "Discovery Engine"
            for w in out.get("warnings", []):
                st.session_state.setdefault("saas_warnings", []).append(w)
            for f in out.get("actionable_findings", []):
                add_finding(f.get("title", "Finding"), f.get("detail", ""))
        except Exception as exc:
            st.warning(f"Discovery failed: {exc}")
            return
    results = st.session_state.get("discovery_results")
    if not results:
        st.info("Run full discovery pipeline.")
        return
    st.metric("Status", results.get("status", "unknown"))
    lb = safe_get(results, "benchmark_results", "leaderboard")
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        from mbsi.visualization.benchmark_plots import plot_leaderboard_bars
        render_interactive_plot(plot_leaderboard_bars(lb), title="Discovery Benchmark", module="discovery")
