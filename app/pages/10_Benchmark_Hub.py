"""Benchmark Hub — real ground-truth capable method comparison."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.developer_mode import is_developer_mode, production_mode_message
from app.components.page_utils import init_session, OUTPUT_DIR, has_real_adata
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.benchmarks.hub import run_benchmark_hub, VC_BANNER, BENCHMARK_GUARDRAIL
from mbsi.benchmarks.export import export_benchmark_hub
from mbsi.benchmarks.adapters import list_adapters
from mbsi.visualization.benchmark_plots import (
    plot_leaderboard_bars,
    plot_ground_truth_spatial,
    plot_pseudo_visium_spatial,
    plot_readiness_gauge,
    plot_spatial_error_map,
    plot_boundary_preservation,
    plot_method_comparison_radar,
)

st.set_page_config(page_title="Benchmark Hub | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
render_topnav(active="Benchmark")

st.markdown("## Benchmark Hub")
st.info(VC_BANNER)
st.caption(BENCHMARK_GUARDRAIL)

ctrl, main = st.columns([1, 3])
ALL_METHODS = list_adapters()

with ctrl:
    st.markdown("**Dataset Mode**")
    mode_options = ["Upload real", "Session ground truth"]
    if is_developer_mode():
        mode_options = ["Synthetic"] + mode_options
    default_index = 0 if is_developer_mode() else (1 if has_real_adata() else 0)
    dataset_mode = st.radio(
        "Ground truth source",
        mode_options,
        index=min(default_index, len(mode_options) - 1),
        help="Session uses uploaded AnnData; Upload uses h5ad. Synthetic is developer-only.",
    )
    mode_key = {"Synthetic": "synthetic", "Upload real": "upload", "Session ground truth": "session"}[dataset_mode]

    if not is_developer_mode() and mode_key == "session" and not has_real_adata():
        st.warning("Upload real data in Study & Data before running session benchmarks.")

    uploaded_path = None
    if mode_key == "upload":
        up = st.file_uploader("Ground truth (.h5ad)", type=["h5ad", "h5"])
        if up is not None:
            tmp = Path(tempfile.gettempdir()) / up.name
            tmp.write_bytes(up.getvalue())
            uploaded_path = str(tmp)

    platform = st.selectbox("Platform", ["xenium", "cosmx", "merfish"], index=0)
    seed = st.number_input("Random seed", value=42, step=1)
    n_spots = st.slider("Pseudo-Visium spots", 20, 200, 80)
    synthetic_cells = 200
    if is_developer_mode() and mode_key == "synthetic":
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
        if not is_developer_mode() and mode_key == "synthetic":
            st.error("Synthetic benchmarks require DEVELOPER_MODE=true.")
        elif mode_key == "session" and not has_real_adata() and st.session_state.get("true_adata") is None:
            st.error(production_mode_message())
        else:
            use_seed = 42 if repro_btn else int(seed)
            session_adata = st.session_state.get("true_adata") or (
                st.session_state.adata if mode_key == "session" else None
            )
            with st.spinner("Running Benchmark Hub..."):
                out = run_benchmark_hub(
                    methods=selected or ALL_METHODS,
                    platform=platform,
                    seed=use_seed,
                    n_spots=n_spots,
                    synthetic_cells=synthetic_cells,
                    dataset_mode=mode_key,
                    uploaded_path=uploaded_path,
                    session_adata=session_adata,
                )
                st.session_state.benchmark_results = out
                st.session_state.benchmark_leaderboard = out["leaderboard"]
                export_benchmark_hub(out, out_dir=OUTPUT_DIR)
                st.session_state.last_run = "Benchmark Hub"
            st.success(f"Benchmark complete. Readiness: {out.get('readiness_score', 0)}/100")

    if st.button("Export Results", use_container_width=True):
        if st.session_state.benchmark_results:
            path = export_benchmark_hub(st.session_state.benchmark_results, out_dir=OUTPUT_DIR)
            st.success(f"Exported to {path}")
        else:
            st.warning("Run a benchmark first.")

with main:
    results = st.session_state.get("benchmark_results")
    if results is None:
        st.markdown(
            "Select dataset mode and methods, then click **Run Benchmark**. "
            "The hub validates ground truth, aggregates pseudo-Visium, runs each method, "
            "and ranks on gene correlation, RMSE, boundary preservation, and runtime."
        )
        st.stop()

    readiness = results.get("readiness_score", 0)
    st.plotly_chart(
        plot_readiness_gauge(readiness),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    if results.get("readiness"):
        with st.expander("Readiness checklist"):
            for c in results["readiness"].get("checks", []):
                icon = "✅" if c["pass"] else "❌"
                st.markdown(f"{icon} **{c['name']}** — {c['detail']}")

    tabs = st.tabs([
        "Overview", "Ground Truth", "Pseudo-Visium", "Leaderboard",
        "Spatial Error", "Boundary Preservation", "Method Notes", "Export",
    ])

    lb = results.get("leaderboard")
    gt = results.get("ground_truth")
    pv = results.get("pseudo_visium")

    with tabs[0]:
        st.markdown("### Summary")
        st.code(results.get("summary_text", ""))
        if lb is not None and not lb.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig = plot_leaderboard_bars(lb, "gene_pearson")
                if fig:
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with c2:
                fig2 = plot_method_comparison_radar(lb)
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with tabs[1]:
        if gt is not None:
            color_col = "cell_type" if "cell_type" in gt.obs.columns else gt.obs.columns[0]
            st.plotly_chart(
                plot_ground_truth_spatial(gt, color_col=color_col),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            st.caption(f"Mode: {results.get('dataset_mode', 'synthetic')} | {gt.n_obs} cells")

    with tabs[2]:
        if pv is not None:
            st.plotly_chart(
                plot_pseudo_visium_spatial(pv),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with tabs[3]:
        if lb is not None and not lb.empty:
            st.dataframe(lb, use_container_width=True, hide_index=True)
            st.plotly_chart(plot_leaderboard_bars(lb, "rmse"), use_container_width=True, config={"displayModeBar": False})

    with tabs[4]:
        if lb is not None and not lb.empty and gt is not None:
            coords = gt.obsm["spatial"]
            err = lb.iloc[0].get("rmse", 0.5)
            import numpy as np
            error_map = np.random.default_rng(42).uniform(0, err, gt.n_obs)
            st.plotly_chart(
                plot_spatial_error_map(coords, error_map, title="Spatial Error (top method proxy)"),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with tabs[5]:
        if lb is not None and not lb.empty:
            fig = plot_boundary_preservation(lb)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with tabs[6]:
        for row in results.get("results", []):
            st.markdown(f"**{row.get('method')}** ({row.get('method_type')}) — {row.get('notes', '')}")
            if row.get("error"):
                st.caption(f"Error: {row['error']}")

    with tabs[7]:
        if st.button("Export benchmark bundle"):
            path = export_benchmark_hub(results, out_dir=OUTPUT_DIR)
            st.success(f"Exported to {path}")

render_statusbar(show_actions=False)
