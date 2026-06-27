"""
FastAPI routes for MBSI Studio API.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

import anndata as ad
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from mbsi.api.schemas import (
    UploadResponse,
    MBSIResponse,
    ValidationResponse,
    BenchmarkResponse,
    ErrorResponse
)
from mbsi.reconstruction.solver import run_mbsi
from mbsi.benchmarks.metrics import compute_all_metrics
from mbsi.benchmarks.ablation import run_ablation_suite


from mbsi.api.job_store import get_job, job_exists, save_job, update_job

async def upload_file(
    file: UploadFile = File(...),
    file_type: str = "h5ad"
) -> UploadResponse:
    """
    Upload spatial transcriptomics data file.
    """
    job_id = str(uuid.uuid4())
    
    # Create job directory
    job_dir = Path("data/uploads") / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file
    file_path = job_dir / file.filename
    with open(file_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    # Load and validate data
    try:
        if file_type == "h5ad":
            adata = ad.read_h5ad(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        job_meta = {
            "status": "uploaded",
            "file_path": str(file_path),
            "file_type": file_type,
            "n_spots": adata.n_obs,
            "n_genes": adata.n_vars,
        }
        save_job(job_id, job_meta)
        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_type=file_type,
            n_spots=adata.n_obs,
            n_genes=adata.n_vars
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")


def run_mbsi_endpoint(request: dict) -> MBSIResponse:
    """
    Run MBSI reconstruction.
    """
    from mbsi.api.schemas import MBSIRequest
    
    req = MBSIRequest(**request)
    job_id = req.job_id
    
    # Check job exists
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    job = get_job(job_id, load_adata=True)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "uploaded":
        raise HTTPException(status_code=400, detail="Job already processed or invalid")
    
    try:
        # Get spot data
        spot_adata = job["adata"]
        
        # Run reconstruction
        reconstructed = run_mbsi(
            spot_adata,
            n_cells_per_spot=req.n_cells_per_spot,
            gamma=req.gamma,
            epsilon=req.epsilon,
            lambda_sheaf=req.lambda_sheaf,
            rho1=req.rho1,
            rho2=req.rho2,
            max_iter=req.max_iter,
            use_sheaf=req.use_sheaf,
            use_anisotropic=req.use_anisotropic,
            k_graph=req.k_graph,
            random_state=req.random_state
        )
        
        # Save results
        output_dir = Path("data/outputs") / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        reconstructed_path = output_dir / "reconstructed.h5ad"
        reconstructed.write_h5ad(reconstructed_path)
        
        update_job(job_id, {
            "status": "completed",
            "reconstructed_path": str(reconstructed_path),
            "parameters": reconstructed.uns['parameters'],
            "convergence": reconstructed.uns['convergence'],
        })
        
        return MBSIResponse(
            job_id=job_id,
            status="completed",
            n_cells=reconstructed.n_obs,
            n_genes=reconstructed.n_vars,
            parameters=reconstructed.uns['parameters'],
            convergence=reconstructed.uns['convergence']
        )
        
    except Exception as e:
        update_job(job_id, {"status": "failed", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Reconstruction failed: {str(e)}")


def validate_endpoint(request: dict) -> ValidationResponse:
    """
    Validate reconstruction against ground truth.
    """
    from mbsi.api.schemas import ValidationRequest
    
    req = ValidationRequest(**request)
    job_id = req.job_id
    
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    job = get_job(job_id, load_adata=True, load_reconstructed=True)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if "reconstructed_path" not in job:
        raise HTTPException(status_code=400, detail="No reconstruction available")
    
    try:
        reconstructed = job["reconstructed"]
        
        # If true data provided, load it
        if req.true_adata_path:
            true_adata = ad.read_h5ad(req.true_adata_path)
        else:
            # Use original spot data as reference (not ideal but works for demo)
            true_adata = job["adata"]
        
        # Compute metrics
        metrics = compute_all_metrics(true_adata, reconstructed)
        
        return ValidationResponse(
            job_id=job_id,
            metrics=metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


def benchmark_endpoint(request: dict) -> BenchmarkResponse:
    """
    Run benchmarking and ablation studies.
    """
    from mbsi.api.schemas import BenchmarkRequest
    
    req = BenchmarkRequest(**request)
    job_id = req.job_id
    
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    job = get_job(job_id, load_adata=True, load_reconstructed=True)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if "reconstructed_path" not in job:
        raise HTTPException(status_code=400, detail="No reconstruction available")
    
    try:
        reconstructed = job["reconstructed"]
        spot_adata = job["adata"]
        
        # Compute basic metrics
        metrics = compute_all_metrics(spot_adata, reconstructed)
        
        # Run ablation if requested
        ablation_results = None
        if req.run_ablation:
            # For MVP, skip full ablation (requires ground truth)
            ablation_results = {"message": "Ablation requires ground truth data"}
        
        return BenchmarkResponse(
            job_id=job_id,
            metrics=metrics,
            ablation_results=ablation_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


def download_file(job_id: str, file_type: str = "reconstructed"):
    """
    Download results file.
    """
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if file_type == "reconstructed":
        if "reconstructed_path" not in job:
            raise HTTPException(status_code=404, detail="No reconstruction file available")
        file_path = job["reconstructed_path"]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown file type: {file_type}")
    
    return FileResponse(
        file_path,
        filename=f"{job_id}_{file_type}.h5ad",
        media_type="application/octet-stream"
    )
