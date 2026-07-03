"""TME Intelligence — tumor microenvironment niche analysis."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.developer_mode import is_developer_mode, production_mode_message
from app.components.page_utils import init_session, ensure_adata, OUTPUT_DIR, has_real_adata
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.tme import (
    run_tme_analysis,
    export_tme_results,
    generate_tme_report,
    make_tme_demo_adata,
    TME_MARKER_SETS,
    TME_GUARDRAIL,
)
from mbsi.reports import generate_spatial_biomarker_report, BIOMARKER_DISCLAIMER
from mbsi.visualization.tme_plots import plot_niche_map, plot_niche_summary

st.set_page_config(page_title="TME Intelligence | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
ensure_adata(show_warning=False)

render_topnav(active="TME")

st.markdown("## Tumor Microenvironment Intelligence")
st.caption(TME_GUARDRAIL)
st.caption(BIOMARKER_DISCLAIMER)

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
    use_demo = False
    if is_developer_mode():
        use_demo = st.checkbox("Use synthetic TME demo", value=False, key="tme_demo")
    elif not has_real_adata():
        st.warning(production_mode_message())
    st.markdown("**Marker Programs**")
    for prog, spec in TME_MARKER_SETS.items():
        genes = [g for k, v in spec.items() if k != "label" and isinstance(v, list) for g in v]
        st.caption(f"**{spec.get('label', prog)}**: {', '.join(genes[:4])}...")

    if st.button("Run TME Analysis", type="primary", use_container_width=True):
        if use_demo and is_developer_mode():
            adata = make_tme_demo_adata(seed=42)
        else:
            adata = st.session_state.adata
        if adata is None or (not use_demo and not has_real_adata()):
            st.error("No real data loaded — upload in Study & Data first.")
        else:
            with st.spinner("Detecting TME niches..."):
                results = run_tme_analysis(adata)
                st.session_state.tme_results = results
                export_tme_results(results, OUTPUT_DIR)
                generate_tme_report(results, OUTPUT_DIR)
                st.session_state.last_run = "TME analysis"
            st.success(f"Detected {len(results['summary'])} niche types.")

    if st.button("Download Spatial Biomarker Report", use_container_width=True):
        if st.session_state.get("tme_results"):
            bench = st.session_state.get("benchmark_results")
            comm = st.session_state.get("communication_results")
            path = generate_spatial_biomarker_report(bench, comm, st.session_state.tme_results, OUTPUT_DIR)
            st.success(f"Report saved: {path}")
        else:
            st.warning("Run TME analysis first.")

with main:
    results = st.session_state.get("tme_results")
    if results is None:
        st.info(
            "Run TME Analysis to auto-detect immune exclusion, TLS-like niches, "
            "CAF barriers, hypoxia, angiogenesis, and invasive fronts."
        )
        st.stop()

    overview, programs, niches_tab, biomarkers_tab = st.tabs(
        ["Overview", "Marker Programs", "Niche Maps", "Biomarkers"]
    )

    with overview:
        st.plotly_chart(
            plot_niche_summary(results["summary"]),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.dataframe(results["summary"], use_container_width=True, hide_index=True)

    with programs:
        ps = results.get("program_summary")
        if ps is not None and not ps.empty:
            st.dataframe(ps, use_container_width=True, hide_index=True)
        else:
            st.caption("Program scores included after pipeline run.")

    with niches_tab:
        coords = results["adata"].obsm["spatial"]
        tabs = st.tabs([label for _, label in NICHE_TABS])
        for tab, (key, label) in zip(tabs, NICHE_TABS):
            with tab:
                niche = results["niches"][key]
                st.metric(f"{label} spots", niche["n_niches"])
                st.plotly_chart(
                    plot_niche_map(coords[:, 0], coords[:, 1], niche["score"], title=label),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

    with biomarkers_tab:
        st.dataframe(results["biomarkers"].head(20), use_container_width=True, hide_index=True)

render_statusbar(show_actions=False)
