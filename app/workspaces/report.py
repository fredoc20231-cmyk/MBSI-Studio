"""Report workspace."""

import streamlit as st
from app.components.page_utils import OUTPUT_DIR
from mbsi.reports.final_report import create_data_bundle, generate_final_html_report, generate_final_pdf_report
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs


def _generate(kind: str) -> None:
    entries = get_notebook_entries()
    if not entries and st.session_state.get("analysis_results") is None:
        st.warning("Notebook is empty — run upload/analysis or discovery first.")
    if kind == "html":
        path = generate_final_html_report(OUTPUT_DIR)
        st.success(f"HTML report: {path}")
    elif kind == "pdf":
        path = generate_final_pdf_report(OUTPUT_DIR)
        st.info(f"PDF path: {path}")
    elif kind == "bundle":
        path = create_data_bundle(OUTPUT_DIR)
        st.success(f"Bundle: {path}")


def render():
    using_demo = st.session_state.get("using_synthetic_demo", True)
    platform = st.session_state.get("mbsi_platform")
    readiness = st.session_state.get("mbsi_readiness", {})
    if using_demo:
        st.warning("Report includes demo/synthetic data — upload real data for production exports.")
    else:
        st.success(
            f"Report will include real data ({platform or 'uploaded'}) — "
            f"{readiness.get('status', 'ready')}"
        )
    ingestion = st.session_state.get("ingestion_result")
    if ingestion and ingestion.get("detection", {}).get("missing"):
        st.caption(f"Ingestion gaps: {', '.join(ingestion['detection']['missing'])}")

    st.markdown(
        '<span class="saas-report-final-badge">Final deliverable</span>',
        unsafe_allow_html=True,
    )
    st.markdown("### Report & Export")
    reg = get_registered_outputs()
    entries = get_notebook_entries()
    analysis = st.session_state.get("analysis_results")
    markers = st.session_state.get("marker_table")
    spatial_stats = st.session_state.get("spatial_stats")

    st.caption(
        f"Notebook: {len(entries)} entries — "
        f"{len(reg.get('figures', []))} figures, {len(reg.get('tables', []))} tables, "
        f"{len(st.session_state.get('findings', []))} DOS findings"
    )

    findings = st.session_state.get("findings") or []
    if findings:
        st.markdown("**Discovery findings included in report**")
        top = sorted(findings, key=lambda f: f.get("confidence_score", 0), reverse=True)[:3]
        for f in top:
            st.caption(f"• {f.get('title')} [{f.get('confidence_level')}]")

    if analysis:
        st.markdown("**Spatial analysis included**")
        qc = analysis.get("qc_summary")
        if qc is not None and hasattr(qc, "empty") and not qc.empty:
            st.caption(f"QC summary: {len(qc)} rows")
        if markers is not None and hasattr(markers, "empty") and not markers.empty:
            st.caption(f"Markers: {len(markers)} rows")
        if spatial_stats is not None and hasattr(spatial_stats, "empty") and not spatial_stats.empty:
            st.caption(f"Spatial stats: {len(spatial_stats)} genes")

    action = st.session_state.pop("ribbon_action", None)
    if action == "gen_html":
        _generate("html")
    elif action == "gen_pdf":
        _generate("pdf")
    elif action == "gen_bundle":
        _generate("bundle")

    if st.button("Generate HTML Report", type="primary", key="ws_gen_html"):
        _generate("html")
    if st.button("Generate PDF (fallback)", key="ws_gen_pdf"):
        _generate("pdf")
    if st.button("Create data bundle", key="ws_gen_bundle"):
        _generate("bundle")
