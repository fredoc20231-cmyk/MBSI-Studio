"""Per-sample upload state — sync, ingest, and Start Analysis helpers (testable)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import anndata as ad
import pandas as pd

from mbsi.schema.technology import (
    UI_TECHNOLOGY_OPTIONS,
    get_technology,
    is_milestone_platform,
    technology_from_label,
)


def default_sample_upload_entry(sample_id: str, technology_key: str) -> Dict[str, Any]:
    return {
        "sample_id": sample_id,
        "technology": technology_key,
        "uploaded_file_name": "",
        "status": "not_uploaded",
        "adata_path": "",
        "dataset_id": "",
        "warnings": [],
    }


def resolve_sample_technology(tech_value: Any, global_technology_key: str = "") -> str:
    """Map sample-table technology label or key to a Milestone 1 technology key."""
    if tech_value is not None and str(tech_value).strip():
        raw = str(tech_value).strip()
        key = technology_from_label(raw)
        if key:
            return key
        lowered = raw.lower()
        if is_milestone_platform(lowered):
            return lowered
        for label, k in UI_TECHNOLOGY_OPTIONS:
            if label.lower() == lowered or k == lowered:
                return k
    if is_milestone_platform(global_technology_key):
        return global_technology_key
    return global_technology_key or "generic_h5ad"


def sync_sample_uploads(
    sample_metadata: Any,
    existing_uploads: Optional[Dict[str, Dict[str, Any]]],
    global_technology_key: str = "",
) -> Dict[str, Dict[str, Any]]:
    """Sync ``sample_uploads`` when ``num_samples`` or ``sample_metadata`` changes."""
    uploads = dict(existing_uploads or {})
    if sample_metadata is None:
        return uploads

    if isinstance(sample_metadata, pd.DataFrame):
        if sample_metadata.empty:
            return {}
        rows = sample_metadata.to_dict("records")
    elif isinstance(sample_metadata, list):
        rows = sample_metadata
    else:
        return uploads

    current_ids: set[str] = set()
    for row in rows:
        sid = str(row.get("sample_id", "")).strip()
        if not sid:
            continue
        current_ids.add(sid)
        tech_key = resolve_sample_technology(row.get("technology"), global_technology_key)
        if sid not in uploads:
            uploads[sid] = default_sample_upload_entry(sid, tech_key)
        else:
            uploads[sid]["sample_id"] = sid
            uploads[sid]["technology"] = tech_key

    for sid in list(uploads.keys()):
        if sid not in current_ids:
            del uploads[sid]

    return uploads


def required_files_for_technology(tech_key: str) -> List[str]:
    spec = get_technology(tech_key)
    if spec is None:
        return ["Upload spatial data file for this sample"]
    return list(spec.required_files)


def upload_file_types_for_technology(tech_key: str) -> List[str]:
    if tech_key == "visium":
        return ["zip"]
    if tech_key == "xenium":
        return ["zip"]
    if tech_key == "generic_h5ad":
        return ["h5ad", "zip", "csv"]
    return ["zip", "h5ad", "csv"]


def status_label(status: str) -> str:
    labels = {
        "not_uploaded": "Not uploaded",
        "uploaded": "Uploaded",
        "ingested": "Ingested",
        "error": "Error",
    }
    return labels.get(status, status.replace("_", " ").title())


def _resolve_effective_technology(
    technology_key: str,
    sample_uploads: Optional[Dict[str, Dict[str, Any]]],
) -> str:
    """Prefer explicit technology; fall back to first ingested sample's platform."""
    if is_milestone_platform(technology_key) or technology_key in ("csv_matrix", "generic_h5ad"):
        return technology_key
    for upload in (sample_uploads or {}).values():
        if upload.get("status") != "ingested":
            continue
        candidate = str(upload.get("technology") or upload.get("platform") or "").strip()
        if is_milestone_platform(candidate) or candidate in ("csv_matrix", "generic_h5ad"):
            return candidate
    return technology_key or UI_TECHNOLOGY_OPTIONS[0][1]


def _has_project_identity(
    project_metadata: Dict[str, Any],
    project_name: str = "",
) -> bool:
    title = str(project_metadata.get("project_title") or "").strip()
    bio_q = str(project_metadata.get("biological_question") or "").strip()
    name = str(project_name or project_metadata.get("project_name") or "").strip()
    if title or bio_q:
        return True
    return bool(name and name.lower() not in {"no project loaded", "untitled project"})


def can_start_analysis(
    project_metadata: Optional[Dict[str, Any]],
    sample_metadata: Any,
    sample_uploads: Optional[Dict[str, Dict[str, Any]]],
    technology_key: str,
    *,
    project_name: str = "",
) -> Tuple[bool, List[str], List[str]]:
    """Return (enabled, hard_missing, soft_warnings) for Start Analysis."""
    missing: List[str] = []
    warnings: List[str] = []
    meta = project_metadata or {}

    ingested = any(u.get("status") == "ingested" for u in (sample_uploads or {}).values())
    has_identity = _has_project_identity(meta, project_name)
    if not has_identity:
        if ingested:
            warnings.append("Add a project title or biological question for reproducible reports.")
        else:
            missing.append("project title, biological question, or project name")

    table_ok = False
    if isinstance(sample_metadata, pd.DataFrame):
        table_ok = not sample_metadata.empty and sample_metadata["sample_id"].notna().all()
    elif isinstance(sample_metadata, list):
        table_ok = len(sample_metadata) > 0
    if not table_ok:
        missing.append("sample metadata table")

    if not ingested:
        missing.append("at least one ingested sample")

    effective_tech = _resolve_effective_technology(technology_key, sample_uploads)
    tech_ok = is_milestone_platform(effective_tech) or effective_tech in ("csv_matrix", "generic_h5ad")
    if not tech_ok:
        missing.append("milestone platform (Visium, Xenium, or Generic)")

    return len(missing) == 0, missing, warnings


def get_primary_ingested_sample(
    sample_uploads: Optional[Dict[str, Dict[str, Any]]],
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    if not sample_uploads:
        return None, None
    for sid, upload in sample_uploads.items():
        if upload.get("status") == "ingested":
            return sid, upload
    return None, None


def _technology_hint_for_path(path: Path, technology_key: str) -> str:
    suffix = path.suffix.lower()
    if technology_key in ("visium", "xenium"):
        return technology_key
    if suffix == ".h5ad":
        return "generic_h5ad"
    if suffix == ".csv":
        return "generic_h5ad"
    if suffix == ".zip":
        return technology_key if is_milestone_platform(technology_key) else "visium"
    return technology_key or "generic_h5ad"


def ingest_sample_file(
    source_path: Path,
    *,
    sample_id: str,
    technology_key: str,
    uploaded_file_name: str,
) -> Dict[str, Any]:
    """Ingest one sample file via ``ingest_dataset`` and return upload state update."""
    from mbsi.io.ingest_universal import ingest_dataset

    hint = _technology_hint_for_path(source_path, technology_key)
    dataset_id = f"{sample_id}-{uuid4().hex[:8]}"

    try:
        result = ingest_dataset(source_path, technology_hint=hint, dataset_id=dataset_id)
    except Exception as exc:
        return {
            **default_sample_upload_entry(sample_id, technology_key),
            "uploaded_file_name": uploaded_file_name,
            "status": "error",
            "warnings": [str(exc)],
        }

    if not result.adata_path:
        return {
            **default_sample_upload_entry(sample_id, technology_key),
            "uploaded_file_name": uploaded_file_name,
            "status": "error",
            "dataset_id": result.dataset_id,
            "warnings": list(result.warnings) or ["Ingestion did not produce AnnData"],
        }

    adata = ad.read_h5ad(result.adata_path)
    adata.obs["sample_id"] = sample_id

    return {
        "sample_id": sample_id,
        "technology": technology_key,
        "uploaded_file_name": uploaded_file_name,
        "status": "ingested",
        "adata_path": result.adata_path,
        "dataset_id": result.dataset_id,
        "warnings": list(result.warnings),
        "platform": result.platform,
        "readiness": dict(result.readiness or {}),
        "compatibility": dict(result.compatibility or {}),
        "metadata": dict(result.metadata or {}),
        "adata": adata,
    }


def apply_ingestion_to_session(
    upload_state: Dict[str, Any],
    *,
    num_samples: int,
) -> Dict[str, Any]:
    """Build session updates after a successful per-sample ingest."""
    adata = upload_state.get("adata")
    sample_id = upload_state["sample_id"]
    updates: Dict[str, Any] = {
        "sample_uploads_patch": {sample_id: {k: v for k, v in upload_state.items() if k != "adata"}},
    }
    if adata is None:
        return updates

    if num_samples == 1:
        updates["adata"] = adata
        updates["ingestion_result"] = {
            "detection": upload_state.get("metadata", {}).get("detection", {}),
            "platform": upload_state.get("platform", upload_state.get("technology")),
            "readiness_score": (upload_state.get("readiness") or {}).get("score", 0),
            "readiness": upload_state.get("readiness", {}),
            "compatibility": upload_state.get("compatibility", {}),
            "source": upload_state.get("adata_path"),
            "sample_id": sample_id,
        }
        updates["mbsi_platform"] = upload_state.get("platform", upload_state.get("technology"))
        updates["using_synthetic_demo"] = False
        from app.components.histology_viewer import extract_histology_from_adata

        if st.session_state.get("uploaded_image") is None:
            img, source, _ = extract_histology_from_adata(adata)
            if img is not None:
                updates["uploaded_image"] = img
                updates["histology_source"] = source
    else:
        updates["sample_adatas"] = {sample_id: adata}
        updates["sample_adata_paths"] = {sample_id: upload_state.get("adata_path", "")}

    return updates
