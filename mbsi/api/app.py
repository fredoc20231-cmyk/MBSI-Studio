"""FastAPI app factory — Builder.io-facing /api routes."""

from __future__ import annotations

import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from mbsi.api import handlers
from mbsi.api.contracts import (
    DatasetInspectRequest,
    DatasetUploadRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ReportGenerateRequest,
    WorkflowRunRequest,
)
from mbsi.api.cors import cors_allow_origins
from mbsi.schema.technology import MILESTONE_1_PLATFORMS


@asynccontextmanager
async def _lifespan(app: FastAPI):
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("data/outputs").mkdir(parents=True, exist_ok=True)
    Path("data/registry/projects").mkdir(parents=True, exist_ok=True)
    Path("data/registry/datasets").mkdir(parents=True, exist_ok=True)
    yield


def create_app(*, include_legacy: bool = False) -> FastAPI:
    """Create FastAPI application with Builder.io contract routes."""
    app = FastAPI(
        title="MBSI Studio API",
        description="Physics-Aware Spatial Biology Intelligence Platform",
        version="0.3.0",
        lifespan=_lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "version": "0.3.0", "milestone_1_platforms": list(MILESTONE_1_PLATFORMS)}

    @app.get("/api/technologies")
    async def api_technologies():
        return handlers.list_technologies()

    @app.post("/api/project/create")
    async def api_project_create(body: ProjectCreateRequest):
        return handlers.create_project(body)

    @app.post("/api/project/update")
    async def api_project_update(body: ProjectUpdateRequest):
        return handlers.update_project(body)

    @app.post("/api/dataset/upload")
    async def api_dataset_upload(
        project_id: str = Query(default=""),
        technology_hint: str | None = Query(default=None),
        sample_id: str = Query(default=""),
        file: UploadFile = File(...),
    ):
        suffix = Path(file.filename or "upload.h5ad").suffix or ".h5ad"
        tmp_dir = Path(tempfile.mkdtemp(prefix="mbsi_upload_"))
        dest = tmp_dir / f"upload{suffix}"
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        req = DatasetUploadRequest(
            project_id=project_id,
            technology_hint=technology_hint,
            sample_id=sample_id,
        )
        return handlers.upload_dataset(req, source_path=str(dest))

    @app.post("/api/dataset/inspect")
    async def api_dataset_inspect(body: DatasetInspectRequest):
        return handlers.inspect_dataset(body)

    @app.get("/api/dataset/readiness")
    async def api_dataset_readiness(dataset_id: str = Query(...)):
        return handlers.dataset_readiness(dataset_id)

    @app.post("/api/workflow/run")
    async def api_workflow_run(body: WorkflowRunRequest):
        return handlers.run_workflow(body)

    @app.get("/api/workflow/status")
    async def api_workflow_status(run_id: str = Query(...)):
        return handlers.workflow_status(run_id)

    @app.get("/api/results/list")
    async def api_results_list(dataset_id: str = Query(default="default")):
        return handlers.list_results(dataset_id)

    @app.get("/api/findings/list")
    async def api_findings_list(
        project_id: str = Query(default=""),
        dataset_id: str = Query(default=""),
        run_id: str = Query(default=""),
    ):
        return handlers.list_findings(
            project_id=project_id,
            dataset_id=dataset_id,
            run_id=run_id,
        )

    @app.get("/api/evidence/list")
    async def api_evidence_list(
        project_id: str = Query(default=""),
        dataset_id: str = Query(default=""),
        run_id: str = Query(default=""),
    ):
        return handlers.list_evidence(
            project_id=project_id,
            dataset_id=dataset_id,
            run_id=run_id,
        )

    @app.post("/api/report/generate")
    async def api_report_generate(body: ReportGenerateRequest):
        return handlers.generate_report(body)

    return app


app = create_app()
