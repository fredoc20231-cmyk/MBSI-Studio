"""TME Intelligence — tumor microenvironment niche analysis."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.tme import (
    run_tme_analysis,
    export_tme_results,
    generate_spatial_biomarker_report,
    make_tme_demo_adata,
    TME_GUARDRAIL,
)
from mbsi.visualization.tme_plots import plot_niche_map, plot_niche_summary

st.set_page_config(page_title="TME Intelligence | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
ensure_adata(show_warning=False)

render_topnav(active="TME")

st.markdown("## Tumor Microenvironment Intelligence")
st.caption(TME_GUARDRAIL)
st.caption("Computational hypothesis — not validated clinical biomarkers.")

ctrl, main = st.columns([1, 3])

NICHE_TABS = [
    ("immune_exclusion", "Immune Exclusion"),
    ("tls_like", "TLS-like Niches"),
    ("caf_barriers", "CAF Barriers"),
    ("hypoxic", "Hypoxic Regions"),
    ("angiogenic", "Angiogenic Regions"),
    ("invasive_fronts", "Invasive Fronts"),
]

with ctrl:
    use_demo = st.checkbox("Use synthetic TME demo", value=True, key="tme_demo")
    if st.button("Run TME Analysis", type="primary", use_container_width=True):
        adata = make_tme_demo_adata(seed=42) if use_demo else st.session_state.adata
        with st.spinner("Detecting TME niches..."):
            results = run_tme_analysis(adata)
            st.session_state.tme_results = results
            export_tme_results(results, OUTPUT_DIR)
            report_path = generate_spatial_biomarker_report(results, OUTPUT_DIR)
            st.session_state.tme_report_path = str(report_path)
            st.session_state.last_run = "TME analysis"
        st.success(f"Detected {len(results['summary'])} niche types.")

    if st.button("Download Spatial Biomarker Report", use_container_width=True):
        if st.session_state.get("tme_results"):
            path = generate_spatial_biomarker_report(st.session_state.tme_results, OUTPUT_DIR)
            st.success(f"Report saved: {path}")
        else:
            st.warning("Run TME analysis first.")

with main:
    results = st.session_state.get("tme_results")
    if results is None:
        st.info("Run TME Analysis to auto-detect immune exclusion, TLS-like niches, CAF barriers, hypoxia, angiogenesis, and invasive fronts.")
        st.stop()

    st.plotly_chart(
        plot_niche_summary(results["summary"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.dataframe(results["summary"], use_container_width=True, hide_index=True)

    tabs = st.tabs([label for _, label in NICHE_TABS])
    coords = results["adata"].obsm["spatial"]
    for tab, (key, label) in zip(tabs, NICHE_TABS):
        with tab:
            niche = results["niches"][key]
            st.metric(f"{label} spots", niche["n_niches"])
            st.plotly_chart(
                plot_niche_map(coords[:, 0], coords[:, 1], niche["score"], title=label),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with st.expander("Biomarker candidates"):
        st.dataframe(results["biomarkers"].head(20), use_container_width=True, hide_index=True)

render_statusbar(show_actions=False)
