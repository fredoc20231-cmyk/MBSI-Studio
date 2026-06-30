"""Benchmark workspace."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.components.page_header import render_page_header
from app.components.safe import safe_get
from app.workspaces._helpers import add_finding, add_warning, demo_banner, safe_register_table


def _run_benchmark() -> None:
    try:
        from mbsi.benchmarks.hub import run_benchmark_hub
        methods = st.session_state.get("rb_benchmark_methods", ["mbsi", "tangram"])
        spots = int(st.session_state.get("rb_benchmark_spots", 40))
        out = run_benchmark_hub(methods=methods, seed=42, n_spots=spots, synthetic_cells=100)
        st.session_state.benchmark_results = out
        st.session_state.last_run = "Benchmark Hub"
        add_finding("Benchmark", f"Readiness {out.get('readiness_score', 0)}/100", module="benchmark")
        safe_register_finding(
            f"Benchmark readiness {out.get('readiness_score', 0)}/100",
            section="benchmark",
            module="benchmark",
            title="Benchmark complete",
        )
    except Exception as exc:
        add_warning(str(exc))
        st.warning(f"Benchmark failed: {exc}")


def render():
    demo_banner()
    action = st.session_state.pop("ribbon_action", None)
    if action == "run_benchmark":
        _run_benchmark()
    elif action == "export_benchmark":
        st.toast("Benchmark summary queued for report export.")

    render_page_header(
        "Benchmark Hub",
        "Compare reconstruction methods on shared gene panels and readiness scores.",
        icon="⚖️",
    )
    if st.button("Run Benchmark (demo)", type="primary", key="ws_run_benchmark"):
        _run_benchmark()

    results = st.session_state.get("benchmark_results")
    if not results:
        st.info("Run benchmark to compare reconstruction methods.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Benchmark mode", results.get("benchmark_mode", "unknown"))
    c2.metric("Shared genes", results.get("n_shared_genes", "—"))
    c3.metric("Cell labels", "Yes" if results.get("has_cell_type_labels") else "No")
    c4.metric("Ground truth", "Yes" if results.get("has_ground_truth") else "No")
    if results.get("n_dropped_genes") is not None:
        st.caption(f"Dropped genes (truth − recon overlap): {results.get('n_dropped_genes', 0)}")

    lb = safe_get(results, "leaderboard")
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        safe_register_table("benchmark", "leaderboard", lb)
        st.dataframe(lb, use_container_width=True, hide_index=True)
        from mbsi.visualization.benchmark_plots import plot_leaderboard_bars
        render_interactive_plot(plot_leaderboard_bars(lb), title="Leaderboard", module="benchmark", key="bench_leaderboard")
    else:
        st.info("No leaderboard data.")
