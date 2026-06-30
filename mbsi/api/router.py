"""Pure-function API router — mountable from FastAPI or tests."""

from __future__ import annotations

from typing import Any, Dict

from mbsi.api import handlers
from mbsi.api.contracts import (
    DatasetInspectRequest,
    DatasetUploadRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ReportGenerateRequest,
    WorkflowRunRequest,
)


def route(method: str, path: str, body: Dict[str, Any] | None = None, **query) -> Dict[str, Any]:
    """Dispatch API contract routes by method/path."""
    body = body or {}
    if method == "POST" and path == "/api/project/create":
        return handlers.create_project(ProjectCreateRequest(**body)).model_dump()
    if method == "POST" and path == "/api/project/update":
        return handlers.update_project(ProjectUpdateRequest(**body)).model_dump()
    if method == "POST" and path == "/api/dataset/upload":
        source = body.pop("source_path", "")
        req = DatasetUploadRequest(**body)
        return handlers.upload_dataset(req, source_path=source).model_dump()
    if method == "POST" and path == "/api/dataset/inspect":
        return handlers.inspect_dataset(DatasetInspectRequest(**body)).model_dump()
    if method == "GET" and path == "/api/dataset/readiness":
        return handlers.dataset_readiness(str(query.get("dataset_id", ""))).model_dump()
    if method == "POST" and path == "/api/workflow/run":
        return handlers.run_workflow(WorkflowRunRequest(**body)).model_dump()
    if method == "GET" and path == "/api/workflow/status":
        return handlers.workflow_status(str(query.get("run_id", ""))).model_dump()
    if method == "GET" and path == "/api/results/list":
        return handlers.list_results(str(query.get("dataset_id", "default"))).model_dump()
    if method == "GET" and path == "/api/findings/list":
        return handlers.list_findings(
            project_id=str(query.get("project_id", "")),
            dataset_id=str(query.get("dataset_id", "")),
            run_id=str(query.get("run_id", "")),
        ).model_dump()
    if method == "GET" and path == "/api/evidence/list":
        return handlers.list_evidence(
            project_id=str(query.get("project_id", "")),
            dataset_id=str(query.get("dataset_id", "")),
            run_id=str(query.get("run_id", "")),
        ).model_dump()
    if method == "POST" and path == "/api/report/generate":
        return handlers.generate_report(ReportGenerateRequest(**body)).model_dump()
    raise ValueError(f"Unknown route: {method} {path}")
