"""Report & Export workspace — notebook, HTML/PDF, bundle, downloads."""

import streamlit as st

from app.components.page_header import render_page_header
from app.components.page_utils import OUTPUT_DIR
from app.components.results_notebook import render_results_notebook
from mbsi.reports.final_report import create_data_bundle, generate_final_html_report, generate_final_pdf_report
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs
from mbsi.schema.report import ReportMetadata
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.workflows.report import run_report_workflow


def _generate(kind: str) -> None:
    from mbsi.reports.final_report import _session_snapshot

    snap = _session_snapshot()
    run = run_report_workflow(OUTPUT_DIR, snapshot=snap, export_type=kind)
    st.session_state.run_outputs["report_export"] = run.to_dict()
    if run.status == "success":
        st.success(f"Export complete: {run.outputs.get('path')}")
    else:
        st.warning(run.warnings[0] if run.warnings else "Export failed")


def render():
    using_demo = st.session_state.get("using_synthetic_demo", True)
    if using_demo:
        st.warning("Report includes demo/synthetic data — upload real data for production exports.")

    st.markdown(
        '<span class="saas-report-final-badge">Final deliverable</span>',
        unsafe_allow_html=True,
    )
    render_page_header(
        "Report & Export",
        "Generate notebooks, HTML/PDF reports, and downloadable data bundles.",
        icon="📄",
    )
    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.REPORT_EXPORT.value]
    tabs = st.tabs([s.replace("_", " ").title() for s in substeps])

    with tabs[0]:
        render_results_notebook(compact=False)

    with tabs[1]:
        reg = get_registered_outputs()
        st.caption(f"{len(get_notebook_entries())} notebook entries · {len(reg.get('findings', []))} registered findings")
        if st.button("Generate HTML Report", type="primary", key="ws_gen_html"):
            _generate("html")

    with tabs[2]:
        if st.button("Generate PDF (fallback)", key="ws_gen_pdf"):
            _generate("pdf")

    with tabs[3]:
        if st.button("Create data bundle", key="ws_gen_bundle"):
            _generate("bundle")

    with tabs[4]:
        st.download_button(
            "Download findings JSON (demo)",
            data=str(st.session_state.get("findings", [])),
            file_name="findings.json",
            key="ws_dl_findings",
        )

    meta = ReportMetadata.from_session_snapshot(
        {
            "project_metadata": st.session_state.get("project_metadata"),
            "sample_metadata": (
                st.session_state.sample_metadata.to_dict("records")
                if hasattr(st.session_state.get("sample_metadata"), "to_dict")
                else st.session_state.get("sample_metadata")
            ),
            "findings": st.session_state.get("findings"),
            "evidence": st.session_state.get("evidence"),
            "last_run": st.session_state.get("last_run"),
            "dataset_readiness": st.session_state.get("dataset_readiness"),
            "project_completeness": st.session_state.get("project_completeness"),
        }
    )
    st.caption(f"Report traceability: {len(meta.finding_ids)} findings, {len(meta.evidence_ids)} evidence items")
