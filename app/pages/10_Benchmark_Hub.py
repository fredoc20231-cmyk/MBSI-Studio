"""Benchmark Hub — VC centerpiece for method comparison."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.benchmarks.hub import run_benchmark_hub, VC_BANNER, BENCHMARK_GUARDRAIL
from mbsi.benchmarks.export import export_benchmark_hub
from mbsi.benchmarks.adapters import list_adapters
from mbsi.visualization.benchmark_plots import plot_leaderboard_bars

st.set_page_config(page_title="Benchmark Hub | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()

render_topnav(active="Benchmark Hub")

st.markdown("## Benchmark Hub")
st.info(VC_BANNER)
st.caption(BENCHMARK_GUARDRAIL)

ctrl, main = st.columns([1, 3])

ALL_METHODS = list_adapters()

with ctrl:
    st.markdown("**Configuration**")
    platform = st.selectbox("Platform", ["xenium", "cosmx", "merfish"], index=0)
    seed = st.number_input("Random seed", value=42, step=1)
    n_spots = st.slider("Pseudo-Visium spots", 20, 200, 80)
    synthetic_cells = st.slider("Synthetic cells", 100, 600, 200)

    st.markdown("**Methods**")
    selected = []
    for m in ALL_METHODS:
        default = m in ("mbsi", "tangram", "cell2location")
        if st.checkbox(m.upper(), value=default, key=f"bm_{m}"):
            selected.append(m)

    run_btn = st.button("Run Benchmark", type="primary", use_container_width=True)
    repro_btn = st.button("Reproduce Benchmark (seed=42)", use_container_width=True)

    if run_btn or repro_btn:
        use_seed = 42 if repro_btn else int(seed)
        with st.spinner("Running Benchmark Hub..."):
            out = run_benchmark_hub(
                methods=selected or ALL_METHODS,
                platform=platform,
                seed=use_seed,
                n_spots=n_spots,
                synthetic_cells=synthetic_cells,
            )
            st.session_state.benchmark_results = out
            st.session_state.benchmark_leaderboard = out["leaderboard"]
            export_benchmark_hub(out, out_dir=OUTPUT_DIR)
            st.session_state.last_run = "Benchmark Hub"
        st.success("Benchmark complete.")

    if st.button("Export Results", use_container_width=True):
        if st.session_state.benchmark_results:
            path = export_benchmark_hub(st.session_state.benchmark_results, out_dir=OUTPUT_DIR)
            st.success(f"Exported to {path}")
        else:
            st.warning("Run a benchmark first.")

with main:
    lb = st.session_state.get("benchmark_leaderboard")
    if lb is not None and not lb.empty:
        st.markdown("### Leaderboard")
        st.dataframe(lb, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            fig = plot_leaderboard_bars(lb, "gene_pearson")
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig2 = plot_leaderboard_bars(lb, "rmse")
            if fig2:
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with st.expander("Method notes"):
            for row in st.session_state.benchmark_results.get("results", []):
                st.markdown(f"**{row.get('method')}** ({row.get('method_type')}) — {row.get('notes', '')}")

        st.markdown("### Summary")
        st.code(st.session_state.benchmark_results.get("summary_text", ""))
    else:
        st.markdown(
            """
            Select platform and methods, then click **Run Benchmark**.

            The hub generates synthetic single-cell ground truth, aggregates to pseudo-Visium,
            runs each reconstruction method, and ranks results on gene correlation, RMSE,
            cell-type accuracy, niche/boundary preservation, and runtime.
            """
        )

render_statusbar(show_actions=False)
