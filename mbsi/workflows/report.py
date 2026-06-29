"""Report generation and export workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from mbsi.schema.report import ReportMetadata
from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_report_workflow(
    output_dir: Path,
    snapshot: Optional[Dict[str, Any]] = None,
    export_type: str = "html",
) -> RunRecord:
    try:
        from mbsi.reports.final_report import (
            create_data_bundle,
            generate_final_html_report,
            generate_final_pdf_report,
        )

        snap = snapshot or {}
        meta = ReportMetadata.from_session_snapshot(snap)
        if export_type == "html":
            path = generate_final_html_report(output_dir, snapshot=snap)
        elif export_type == "pdf":
            path = generate_final_pdf_report(output_dir, snapshot=snap)
        elif export_type == "bundle":
            path = create_data_bundle(output_dir, snapshot=snap)
        else:
            return RunRecord.failed(WorkflowModule.REPORT_EXPORT.value, f"unknown export_type: {export_type}")

        meta.output_files.append(str(path))
        return RunRecord.success(
            module=WorkflowModule.REPORT_EXPORT.value,
            inputs={"export_type": export_type},
            outputs={"path": str(path), "report_metadata": meta.to_dict()},
        )
    except Exception as exc:
        return RunRecord.failed(WorkflowModule.REPORT_EXPORT.value, str(exc))
