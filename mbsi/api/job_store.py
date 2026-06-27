"""
File-based job persistence for the MBSI Studio API.

Job metadata is stored as JSON under data/uploads/{job_id}/job.json.
AnnData objects are stored as h5ad files and loaded on demand.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad

JOBS_ROOT = Path("data/uploads")
OUTPUT_ROOT = Path("data/outputs")


def _job_dir(job_id: str) -> Path:
    return JOBS_ROOT / job_id


def _job_meta_path(job_id: str) -> Path:
    return _job_dir(job_id) / "job.json"


def save_job(job_id: str, metadata: Dict[str, Any]) -> None:
    """Persist job metadata to disk."""
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    serializable = {k: v for k, v in metadata.items() if k not in ("adata", "reconstructed")}
    with open(_job_meta_path(job_id), "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, default=str)


def load_job_meta(job_id: str) -> Optional[Dict[str, Any]]:
    """Load job metadata from disk."""
    meta_path = _job_meta_path(job_id)
    if not meta_path.exists():
        return None
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def job_exists(job_id: str) -> bool:
    return _job_meta_path(job_id).exists()


def get_job(job_id: str, load_adata: bool = False, load_reconstructed: bool = False) -> Optional[Dict[str, Any]]:
    """Load job metadata and optionally hydrate AnnData objects."""
    meta = load_job_meta(job_id)
    if meta is None:
        return None

    job = dict(meta)
    if load_adata and "file_path" in job:
        job["adata"] = ad.read_h5ad(job["file_path"])
    if load_reconstructed and "reconstructed_path" in job:
        job["reconstructed"] = ad.read_h5ad(job["reconstructed_path"])
    return job


def update_job(job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge updates into persisted job metadata."""
    meta = load_job_meta(job_id) or {}
    meta.update({k: v for k, v in updates.items() if k not in ("adata", "reconstructed")})
    save_job(job_id, meta)
    return meta
