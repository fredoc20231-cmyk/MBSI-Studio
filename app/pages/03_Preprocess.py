"""Preprocessing & QC page with analytical controls."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, guardrail_banner, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.analysis.pipeline import ANALYSIS_GUARDRAIL
from mbsi.analysis.qc import compute_qc_metrics, filter_in_tissue, qc_summary_table, flag_low_quality_spots
from mbsi.analysis.preprocessing import normalize_log_transform, select_hvgs, scale_for_pca
from mbsi.visualization.analysis_plots import plot_qc_spatial, plot_qc_violin, plot_counts_vs_mito

st.set_page_config(page_title="Preprocess | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_adata(show_warning=False)

render_topnav(active="Preprocess")

st.markdown("### Preprocessing & QC")
st.caption(ANALYSIS_GUARDRAIL)

c1, c2 = st.columns([1, 2])
with c1:
    min_counts = st.slider("Min counts per spot", 0, 2000, 100, key="pp_min_counts")
    min_genes = st.slider("Min genes per spot", 0, 500, 50, key="pp_min_genes")
    max_mt = st.slider("Max mitochondrial %", 0.0, 100.0, 25.0, key="pp_max_mt")
    n_hvg = st.number_input("Highly variable genes", 500, 5000, 2000, step=100, key="pp_n_hvg")
    filter_tissue = st.checkbox("Filter in-tissue spots only", value=True, key="pp_filter_tissue")

    if st.button("Run QC", type="primary", key="pp_run_qc"):
        adata = st.session_state.adata.copy()
        if filter_tissue:
            adata = filter_in_tissue(adata)
        adata = compute_qc_metrics(adata)
        adata = flag_low_quality_spots(adata, min_counts=min_counts, min_genes=min_genes, max_mito=max_mt)
        st.session_state.adata = adata
        st.session_state.preprocessing_params = {
            "min_counts": min_counts,
            "min_genes": min_genes,
            "max_mt_pct": max_mt,
            "n_hvg": n_hvg,
            "filter_tissue": filter_tissue,
        }
        st.session_state.last_run = "Preprocessing QC"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        qc_summary_table(adata).to_csv(OUTPUT_DIR / "qc_summary.csv", index=False)
        st.success(f"QC complete — {int(adata.obs['qc_pass'].sum())}/{adata.n_obs} spots pass filters.")

    if st.button("Normalize + HVG", key="pp_norm_hvg"):
        adata = st.session_state.adata.copy()
        if "qc_pass" in adata.obs.columns:
            adata = adata[adata.obs["qc_pass"]].copy()
        adata = normalize_log_transform(adata)
        adata = select_hvgs(adata, n_top_genes=int(n_hvg))
        adata = scale_for_pca(adata)
        st.session_state.adata = adata
        st.session_state.last_run = "Normalize + HVG"
        st.success(f"Normalized; {int(adata.var['highly_variable'].sum())} HVGs selected.")

with c2:
    if st.session_state.adata is not None:
        adata = st.session_state.adata
        if "total_counts" not in adata.obs.columns:
            adata = compute_qc_metrics(adata)
        st.markdown("**QC summary**")
        st.dataframe(qc_summary_table(adata), use_container_width=True, hide_index=True)
        q1, q2 = st.columns(2)
        with q1:
            st.plotly_chart(plot_qc_spatial(adata, "total_counts"), use_container_width=True, config={"displayModeBar": False})
        with q2:
            st.plotly_chart(plot_counts_vs_mito(adata), use_container_width=True, config={"displayModeBar": False})
        st.plotly_chart(plot_qc_violin(adata), use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Load or upload Visium data to run QC.")

if st.session_state.preprocessing_params:
    st.json(st.session_state.preprocessing_params)

render_statusbar(show_actions=False)
