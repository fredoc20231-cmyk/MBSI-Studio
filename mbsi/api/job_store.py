"""
File-based job persistence for the MBSI Studio API.

Job metadata is stored as JSON under data/uploads/{job_id}/job.json.
AnnData objects are stored as h5ad files and loaded on demand.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad

JOBS_ROOT = Path("data/uploads")
OUTPUT_ROOT = Path("data/outputs")

_JOB_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class InvalidJobIdError(ValueError):
    """Raised when job_id is missing or unsafe for filesystem use."""


def validate_job_id(job_id: str) -> str:
    """Reject path traversal and unsafe characters in job identifiers."""
    if not job_id or not isinstance(job_id, str):
        raise InvalidJobIdError("job_id is required")
    if ".." in job_id or "/" in job_id or "\\" in job_id:
        raise InvalidJobIdError("job_id must not contain path separators")
    if not _JOB_ID_PATTERN.match(job_id):
        raise InvalidJobIdError("job_id contains unsafe characters")
    return job_id


def _safe_child_path(root: Path, *parts: str) -> Path:
    """Resolve a path under root and reject directory escape."""
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise InvalidJobIdError("path escapes allowed storage root") from exc
    return candidate


def resolve_download_path(stored_path: str | Path, *, allowed_roots: tuple[Path, ...] | None = None) -> Path:
    """Ensure a stored file path resolves inside allowed upload/output roots."""
    roots = allowed_roots or (JOBS_ROOT, OUTPUT_ROOT)
    candidate = Path(stored_path).resolve()
    for root in roots:
        root_resolved = root.resolve()
        try:
            candidate.relative_to(root_resolved)
            return candidate
        except ValueError:
            continue
    raise InvalidJobIdError("download path is outside data/uploads or data/outputs")


def _job_dir(job_id: str) -> Path:
    safe_id = validate_job_id(job_id)
    return _safe_child_path(JOBS_ROOT, safe_id)


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
    try:
        return _job_meta_path(job_id).exists()
    except InvalidJobIdError:
        return False


def get_job(job_id: str, load_adata: bool = False, load_reconstructed: bool = False) -> Optional[Dict[str, Any]]:
    """Load job metadata and optionally hydrate AnnData objects."""
    meta = load_job_meta(job_id)
    if meta is None:
        return None

    job = dict(meta)
    if load_adata and "file_path" in job:
        file_path = resolve_download_path(job["file_path"])
        job["adata"] = ad.read_h5ad(file_path)
    if load_reconstructed and "reconstructed_path" in job:
        recon_path = resolve_download_path(job["reconstructed_path"])
        job["reconstructed"] = ad.read_h5ad(recon_path)
    return job


def update_job(job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge updates into persisted job metadata."""
    meta = load_job_meta(job_id) or {}
    meta.update({k: v for k, v in updates.items() if k not in ("adata", "reconstructed")})
    save_job(job_id, meta)
    return meta
