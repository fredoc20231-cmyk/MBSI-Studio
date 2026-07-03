"""Report & Export workspace — notebook, HTML/PDF, bundle, downloads."""

import streamlit as st

from app.components.developer_mode import is_developer_mode, production_mode_message
from app.components.notification_center import push_notification
from app.components.page_header import render_page_header
from app.components.page_utils import OUTPUT_DIR
from app.components.results_notebook import render_results_notebook
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs
from mbsi.schema.report import ReportMetadata
from mbsi.schema.technology import get_technology, is_milestone_platform
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.workflows.report import run_report_workflow


def _generate(kind: str) -> None:
    from mbsi.reports.final_report import _session_snapshot

    snap = _session_snapshot()
    snap["ingestion_result"] = st.session_state.get("ingestion_result")
    snap["analysis_results"] = st.session_state.get("analysis_results")
    snap["marker_table"] = st.session_state.get("marker_table") or snap.get("marker_table")
    snap["spatial_stats"] = st.session_state.get("spatial_stats") or snap.get("spatial_stats")
    run = run_report_workflow(OUTPUT_DIR, snapshot=snap, export_type=kind)
    st.session_state.run_outputs["report_export"] = run.to_dict()
    if run.status == "success":
        path = run.outputs.get("path", "")
        push_notification(
            f"{kind.upper()} report saved{f' to {path}' if path else ''}.",
            title="Report generated",
            level="success",
            source="report_export",
        )
        st.success(f"Export complete: {path}")
    else:
        msg = run.warnings[0] if run.warnings else "Export failed"
        push_notification(msg, title="Report generation failed", level="error", source="report_export")
        st.warning(msg)


def render():
    st.markdown(
        '<span class="saas-report-final-badge">Final deliverable</span>',
        unsafe_allow_html=True,
    )
    render_page_header(
        "Report & Export",
        "Generate notebooks, HTML/PDF reports, and downloadable data bundles.",
        icon="📄",
    )
    tech_key = st.session_state.get("selected_technology", "") or st.session_state.get("mbsi_platform", "")
    if tech_key and not is_milestone_platform(tech_key) and tech_key not in ("csv_matrix", "demo"):
        spec = get_technology(tech_key)
        label = spec.label if spec else tech_key
        st.warning(f"**{label}** is marked **Coming later** — report export for this platform is not in Milestone 1 scope.")
        return
    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.REPORT_EXPORT.value]
    tabs = st.tabs([s.replace("_", " ").title() for s in substeps])

    with tabs[0]:
        render_results_notebook(compact=False)
        if is_developer_mode():
            st.divider()
            st.markdown("#### Results Cockpit (developer)")
            st.caption("Synthetic multi-panel dashboard — requires DEVELOPER_MODE=true.")
            if st.button("Open full-screen Results Cockpit", key="ws_open_cockpit"):
                st.session_state.mbsi_dashboard_mode = True
                st.query_params["dashboard"] = "1"
                st.rerun()
            from app.components.dashboard_cockpit import render_dashboard_cockpit

            render_dashboard_cockpit(show_navbar=False, compact=True)
        else:
            st.caption(production_mode_message())

    with tabs[1]:
        analysis = st.session_state.get("analysis_results")
        if analysis:
            st.caption(
                f"Milestone 1 results: {analysis.get('clusters', {}).get('n_clusters', 0)} clusters · "
                f"platform {analysis.get('platform', '—')}"
            )
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
            "Download findings JSON",
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

