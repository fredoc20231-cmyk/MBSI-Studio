"""FastAPI app factory — Builder.io-facing /api routes."""

from __future__ import annotations

import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from mbsi.api import handlers
from mbsi.api.imaging_routes import router as imaging_router
from mbsi.api.spatial_routes import router as spatial_router
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
from pydantic import BaseModel, Field


class MorphologySTIERequest(BaseModel):
    expression: list[list[float]]
    signatures: list[list[float]]
    morphology: list[list[float]]
    cell_coords: list[list[float]]
    spot_coords: list[list[float]]
    penalty: float = Field(default=1.0, ge=0, le=1e5)
    random_state: int = 0
    max_assignment_distance: float | None = Field(default=None, gt=0)



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
    app.include_router(imaging_router)
    app.include_router(spatial_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def service_index():
        """Friendly response for Render root health checks and browser navigation."""
        return {"service": "MBSI Studio FastAPI", "status": "healthy",
                "health": "/api/health", "openapi": "/openapi.json", "docs": "/docs"}

    @app.get("/health")
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "version": "0.3.0", "milestone_1_platforms": list(MILESTONE_1_PLATFORMS)}

    @app.post("/api/v1/reconstruction/morphology-stie")
    async def morphology_stie(body: MorphologySTIERequest):
        """Small registered-data experimental inference; not ground truth."""
        from mbsi.reconstruction.morphology_stie import fit_morphology_stie
        if (len(body.expression) > 2000 or len(body.morphology) > 10000
                or not body.expression or not body.morphology
                or len(body.expression[0]) > 5000 or len(body.signatures) > 5000
                or len(body.morphology[0]) > 128):
            raise HTTPException(status_code=413, detail="Input exceeds synchronous inference limits")
        try:
            result = fit_morphology_stie(
                body.expression, body.signatures, body.morphology,
                body.cell_coords, body.spot_coords, penalty=body.penalty,
                random_state=body.random_state,
                max_assignment_distance=body.max_assignment_distance,
            )
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "status": "completed", "method": "experimental_morphology_stie",
            "validation_status": "not_benchmarked",
            "spot_abundance": result.spot_abundance.tolist(),
            "cell_probabilities": result.cell_probabilities.tolist(),
            "cell_type_index": result.cell_type_index.tolist(),
            "cell_confidence": result.cell_confidence.tolist(),
            "cell_to_spot": result.cell_to_spot.tolist(),
            "objective_history": result.objective_history,
            "converged": result.converged,
            "warnings": ["Inferred assignments are not observed cell identities.",
                         "Gene order and spatial registration must be verified upstream.",
                         "Not benchmarked against imaging-based single-cell ground truth."],
        }

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
