"""
FastAPI main application for MBSI Studio.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware


def _cors_allow_origins() -> list[str]:
    """Resolve allowed CORS origins from MBSI_CORS_ALLOW_ORIGINS.

    Defaults to "*" for local development. In production set an explicit,
    comma-separated allowlist (e.g. "https://app.example.com").
    """
    raw = os.environ.get("MBSI_CORS_ALLOW_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

from mbsi.api.routes import (
    upload_file,
    run_mbsi_endpoint,
    validate_endpoint,
    benchmark_endpoint,
    download_file
)
from mbsi.api.routes_advanced import (
    segment_endpoint,
    subcellular_endpoint,
    boundaries_endpoint,
    communication_endpoint,
    causal_build_endpoint,
    causal_intervene_endpoint,
    temporal_align_endpoint,
    digital_twin_build_endpoint,
    digital_twin_simulate_endpoint,
    multimodal_fuse_endpoint,
    copilot_query_endpoint,
    export_report_endpoint,
)
from mbsi.api.schemas import (
    HealthResponse, UploadResponse, MBSIResponse, ValidationResponse, BenchmarkResponse,
    CopilotRequest, CopilotResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    import os
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/outputs", exist_ok=True)
    yield
    # Shutdown
    pass


app = FastAPI(
    title="MBSI Studio API",
    description="Physics-Aware Spatial Biology Intelligence Platform",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware. Origins come from MBSI_CORS_ALLOW_ORIGINS
# (default "*" for local dev; set an explicit allowlist in production).
_allow_origins = _cors_allow_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    # credentials cannot be combined with a wildcard origin per the CORS spec
    allow_credentials=_allow_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/readyz")
async def readiness_check():
    """Readiness probe: process is up and able to serve requests."""
    return {"status": "ready", "version": "0.2.0"}


@app.get("/healthz")
async def health_alias():
    """Liveness probe alias (kubernetes-style path)."""
    return {"status": "healthy", "version": "0.2.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.2.0"
    )


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    file_type: str = "h5ad"
):
    """Upload spatial transcriptomics data file."""
    return await upload_file(file, file_type)


@app.post("/run-mbsi", response_model=MBSIResponse)
async def run_mbsi(request: dict):
    """Run MBSI reconstruction."""
    return run_mbsi_endpoint(request)


@app.post("/validate", response_model=ValidationResponse)
async def validate(request: dict):
    """Validate reconstruction against ground truth."""
    return validate_endpoint(request)


@app.post("/benchmark", response_model=BenchmarkResponse)
async def benchmark(request: dict):
    """Run benchmarking."""
    return benchmark_endpoint(request)


@app.get("/download/{job_id}")
async def download(job_id: str, file_type: str = "reconstructed"):
    """Download results file."""
    return download_file(job_id, file_type)


@app.post("/segment")
async def segment(request: dict):
    return segment_endpoint(request)


@app.post("/subcellular")
async def subcellular(request: dict):
    return subcellular_endpoint(request)


@app.post("/boundaries")
async def boundaries(request: dict):
    return boundaries_endpoint(request)


@app.post("/communication")
async def communication(request: dict):
    return communication_endpoint(request)


@app.post("/causal/build")
async def causal_build(request: dict):
    return causal_build_endpoint(request)


@app.post("/causal/intervene")
async def causal_intervene(request: dict):
    return causal_intervene_endpoint(request)


@app.post("/temporal/align")
async def temporal_align(request: dict):
    return temporal_align_endpoint(request)


@app.post("/digital-twin/build")
async def digital_twin_build(request: dict):
    return digital_twin_build_endpoint(request)


@app.post("/digital-twin/simulate")
async def digital_twin_simulate(request: dict):
    return digital_twin_simulate_endpoint(request)


@app.post("/multimodal/fuse")
async def multimodal_fuse(request: dict):
    return multimodal_fuse_endpoint(request)


@app.post("/copilot/query", response_model=CopilotResponse)
async def copilot_query(request: CopilotRequest):
    result = copilot_query_endpoint(request.model_dump())
    return CopilotResponse(**result)


@app.post("/export/report")
async def export_report(request: dict):
    return export_report_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
