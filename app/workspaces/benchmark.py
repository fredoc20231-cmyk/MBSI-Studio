"""Benchmark workspace."""

import streamlit as st
from app.components.safe import safe_plotly, safe_get
from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import demo_banner, add_finding, add_warning
from mbsi.reports.registry import register_table


def render():
    demo_banner()
    st.markdown("### Benchmark Hub")
    if st.button("Run Benchmark (demo)", type="primary"):
        try:
            from mbsi.benchmarks.hub import run_benchmark_hub
            out = run_benchmark_hub(methods=["mbsi", "tangram"], seed=42, n_spots=40, synthetic_cells=100)
            st.session_state.benchmark_results = out
            st.session_state.last_run = "Benchmark Hub"
            add_finding("Benchmark", f"Readiness {out.get('readiness_score', 0)}/100")
        except Exception as exc:
            add_warning(str(exc))
            st.warning(f"Benchmark failed: {exc}")
            return
    results = st.session_state.get("benchmark_results")
    if not results:
        st.info("Run benchmark to compare reconstruction methods.")
        return
    lb = safe_get(results, "leaderboard")
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        register_table("benchmark", "leaderboard", lb)
        st.dataframe(lb, use_container_width=True, hide_index=True)
        from mbsi.visualization.benchmark_plots import plot_leaderboard_bars
        render_interactive_plot(plot_leaderboard_bars(lb), title="Leaderboard", module="benchmark")
    else:
        st.info("No leaderboard data.")
