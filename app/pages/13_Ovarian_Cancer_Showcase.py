"""Ovarian Cancer HGSOC flagship showcase page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.showcase import (
    run_ovarian_showcase_pipeline,
    export_ovarian_showcase,
    generate_ovarian_showcase_report,
    SHOWCASE_GUARDRAIL,
)
from mbsi.visualization.communication_plots import plot_pathway_rankings, plot_signaling_map
from mbsi.visualization.tme_plots import plot_niche_map, plot_niche_summary

st.set_page_config(
    page_title="HGSOC Showcase | MBSI Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session()
inject_styles()
render_topnav(active="HGSOC")

st.markdown(
    """
    <div style="background:linear-gradient(135deg,#1a0a2e 0%,#0d1828 100%);padding:24px;border-radius:12px;margin-bottom:16px;border:1px solid #3d1a5c;">
      <h1 style="color:#ff4f7b;margin:0;">High-Grade Serous Ovarian Cancer</h1>
      <h3 style="color:#f4f7fb;margin:8px 0 0;font-weight:400;">Flagship Demonstration — Integrated Spatial Intelligence</h3>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(SHOWCASE_GUARDRAIL)

if st.button("Run Full Showcase Pipeline", type="primary"):
    with st.spinner("Running integrated HGSOC pipeline..."):
        results = run_ovarian_showcase_pipeline(seed=42)
        st.session_state.ovarian_showcase_results = results
        export_ovarian_showcase(results, OUTPUT_DIR)
        report = generate_ovarian_showcase_report(results, OUTPUT_DIR)
        st.session_state.ovarian_report_path = str(report)
        st.session_state.last_run = "HGSOC showcase"
    st.success("Showcase pipeline complete.")

results = st.session_state.get("ovarian_showcase_results")
if results is None:
    st.info("Click **Run Full Showcase Pipeline** to generate the integrated HGSOC demonstration.")
    st.stop()

tabs = st.tabs(["Overview", "Spatial Map", "Communication", "TME", "Resistance", "Report"])

with tabs[0]:
    st.markdown("### Key Findings (computational hypothesis)")
    for finding in results["findings"].values():
        st.markdown(f"**{finding['label']}**")
        st.caption(f"Hypothesis: {finding['hypothesis']}")
        st.json({k: v for k, v in finding.items() if k not in ("label", "hypothesis")})
        st.markdown("---")

with tabs[1]:
    coords = results["adata"].obsm["spatial"]
    cxcl12_idx = list(results["adata"].var_names).index("CXCL12") if "CXCL12" in results["adata"].var_names else 0
    cxcl12_expr = results["adata"].X[:, cxcl12_idx]
    if hasattr(cxcl12_expr, "toarray"):
        cxcl12_expr = cxcl12_expr.toarray().flatten()
    st.plotly_chart(
        plot_niche_map(coords[:, 0], coords[:, 1], cxcl12_expr, title="CXCL12 Spatial Expression"),
        use_container_width=True, config={"displayModeBar": False},
    )
    if results.get("histology_image") is not None:
        st.image(results["histology_image"], caption="Synthetic H&E histology (demo)", use_container_width=True)

with tabs[2]:
    comm = results["communication"]
    st.dataframe(comm["pathway_rankings"], use_container_width=True, hide_index=True)
    st.plotly_chart(plot_pathway_rankings(comm["pathway_rankings"]), use_container_width=True, config={"displayModeBar": False})
    niche = comm.get("niche_map")
    if niche:
        st.plotly_chart(plot_signaling_map(niche, title="CXCL12-CXCR4 Signaling Flux"), use_container_width=True, config={"displayModeBar": False})

with tabs[3]:
    tme = results["tme"]
    st.plotly_chart(plot_niche_summary(tme["summary"]), use_container_width=True, config={"displayModeBar": False})
    coords = results["adata"].obsm["spatial"]
    c1, c2 = st.columns(2)
    with c1:
        ie = tme["niches"]["immune_exclusion"]
        st.plotly_chart(plot_niche_map(coords[:, 0], coords[:, 1], ie["score"], title="Immune Exclusion"), use_container_width=True, config={"displayModeBar": False})
    with c2:
        caf = tme["niches"]["caf_barriers"]
        st.plotly_chart(plot_niche_map(coords[:, 0], coords[:, 1], caf["score"], title="CAF Barriers"), use_container_width=True, config={"displayModeBar": False})

with tabs[4]:
    resist = results["resistance"]
    st.dataframe(resist.head(30), use_container_width=True, hide_index=True)
    st.plotly_chart(plot_niche_map(resist["x"], resist["y"], resist["platinum_resistance_score"], title="Platinum Resistance"), use_container_width=True, config={"displayModeBar": False})
    st.plotly_chart(plot_niche_map(resist["x"], resist["y"], resist["parp_resistance_score"], title="PARP Resistance"), use_container_width=True, config={"displayModeBar": False})

with tabs[5]:
    report_path = Path(st.session_state.get("ovarian_report_path", OUTPUT_DIR / "ovarian_showcase_report.html"))
    st.markdown(f"**Report:** `{report_path}`")
    if st.button("Regenerate Report"):
        path = generate_ovarian_showcase_report(results, OUTPUT_DIR)
        export_ovarian_showcase(results, OUTPUT_DIR)
        st.success(f"Saved to {path}")
    if report_path.exists():
        st.download_button("Download HTML Report", report_path.read_text(), file_name="ovarian_showcase_report.html")
    st.download_button(
        "Download Summary JSON",
        json.dumps({"findings": results["findings"], "guardrail": SHOWCASE_GUARDRAIL}, indent=2, default=str),
        file_name="ovarian_showcase_summary.json",
    )

render_statusbar(show_actions=False)
