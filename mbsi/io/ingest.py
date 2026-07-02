"""Unified ingestion entry points for SaaS upload."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ad
import pandas as pd

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad
from mbsi.io.visium import load_space_ranger
from mbsi.io.xenium import load_xenium
from mbsi.io.stereo_seq import load_stereo_seq_dataset
from mbsi.schema.technology import get_technology


LOADER_CONTRACT_KEYS = (
    "adata",
    "spatialdata",
    "platform",
    "technology_profile",
    "images",
    "masks",
    "metadata",
    "readiness",
    "compatibility",
    "warnings",
)


def normalize_loader_result(partial: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize partial loader output to unified ingest contract."""
    detection = partial.get("detection") or partial.get("metadata", {}).get("detection", {})
    platform = partial.get("platform", detection.get("platform", "unknown"))
    tech_key = detection.get("technology_key") or platform
    tech = get_technology(tech_key)
    readiness = partial.get("readiness")
    if readiness is None and partial.get("readiness_score") is not None:
        readiness = {"score": partial.get("readiness_score"), "status": partial.get("readiness_status", "unknown")}
    warnings = list(partial.get("warnings") or [])
    if partial.get("limitations"):
        warnings.extend(partial["limitations"])
    if detection.get("missing"):
        warnings.extend([f"Missing: {m}" for m in detection["missing"]])

    return {
        "adata": partial.get("adata"),
        "spatialdata": partial.get("spatialdata"),
        "platform": platform,
        "technology_profile": partial.get("technology_profile") or (tech.to_dict() if tech else {}),
        "images": partial.get("images") or ([partial["image"]] if partial.get("image") else []),
        "masks": partial.get("masks") or ([partial["segmentation"]] if partial.get("segmentation") is not None else []),
        "metadata": {
            "detection": detection,
            "source": partial.get("source"),
            **(partial.get("metadata") or {}),
        },
        "readiness": readiness or {},
        "compatibility": partial.get("compatibility") or get_compatibility_matrix(partial.get("adata"), detection, tech_key),
        "warnings": warnings,
        # Legacy keys preserved for callers
        "detection": detection,
        "readiness_score": partial.get("readiness_score", (readiness or {}).get("score", 0)),
        "source": partial.get("source"),
    }


def ingest_upload(
    *,
    h5ad_path: Optional[Path] = None,
    visium_path: Optional[Path] = None,
    xenium_path: Optional[Path] = None,
    stereo_seq_path: Optional[Path] = None,
    count_matrix: Optional[pd.DataFrame] = None,
    coordinates: Optional[pd.DataFrame] = None,
    file_names: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Ingest uploaded files into AnnData + metadata bundle for session_state.

    Returns unified loader dict (see normalize_loader_result).
    """
    detection = detect_platform(file_names or [])
    adata: Optional[ad.AnnData] = None
    meta: Dict[str, Any] = {}

    if visium_path is not None:
        adata, meta = load_space_ranger(visium_path)
        detection = meta.get("detection", detection)
    elif xenium_path is not None:
        adata, meta = load_xenium(xenium_path)
        detection = meta.get("detection", detection)
    elif stereo_seq_path is not None:
        adata, meta = load_stereo_seq_dataset(stereo_seq_path)
        detection = meta.get("detection", detection)
    elif h5ad_path is not None:
        adata, meta = ingest_h5ad(h5ad_path)
        detection = meta.get("detection", detection)
    elif count_matrix is not None and coordinates is not None:
        adata, meta = ingest_csv_matrix_coords(count_matrix, coordinates)
        detection = meta.get("detection", detection)
    else:
        return normalize_loader_result({
            "detection": detection,
            "readiness_score": 0,
            "readiness": {"status": "No ingestible files"},
            "compatibility": get_compatibility_matrix(None, detection),
            "platform": detection.get("platform", "unknown"),
        })

    platform = meta.get("platform", detection.get("platform", "unknown"))
    score = meta.get("readiness_score", adata.uns.get("mbsi_readiness_score", 0))
    readiness = meta.get("readiness", adata.uns.get("mbsi_readiness", {}))
    compatibility = get_compatibility_matrix(adata, detection)

    partial: Dict[str, Any] = {
        "adata": adata,
        "detection": detection,
        "readiness_score": score,
        "readiness": readiness,
        "compatibility": compatibility,
        "platform": platform,
        "source": meta.get("source"),
        "metadata": meta,
        "images": meta.get("images", []),
        "masks": meta.get("masks", []),
        "spatialdata": meta.get("spatialdata"),
    }
    if platform == "stereo_seq":
        partial["stereo_seq_readiness"] = meta.get("stereo_seq_readiness", readiness)
        partial["stereo_seq"] = meta.get("stereo_seq", {})
        partial["limitations"] = meta.get("limitations", [])
        partial["platform_metadata"] = meta.get("stereo_seq", {})
    return normalize_loader_result(partial)


def load_dataset_from_manifest(
    download_dir: Path | str,
    manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ingest a downloaded dataset directory using manifest metadata.

    Attempts Visium ZIP, Stereo-seq, or h5ad based on detected platform and files on disk.
    """
    from mbsi.io.downloader.inspector import inspect_downloaded_files, update_ingestion_readiness

    root = Path(download_dir)
    detection = inspect_downloaded_files(root)
    readiness_bundle = update_ingestion_readiness(root, detection)
    platform = detection.get("platform", "unknown")
    file_names = detection.get("files", [])

    h5ad_path: Optional[Path] = None
    visium_path: Optional[Path] = None
    stereo_seq_path: Optional[Path] = None

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        low = f.name.lower()
        if low.endswith(".h5ad") and h5ad_path is None:
            h5ad_path = f
        if low.endswith(".zip") and any(k in low for k in ("visium", "spaceranger", "outs")):
            visium_path = f
        if low.endswith((".gef", ".cgef")) or (low.endswith(".zip") and "stereo" in low):
            stereo_seq_path = f

    if platform == "visium" and visium_path is None:
        for f in root.rglob("*.zip"):
            visium_path = f
            break

    result = ingest_upload(
        h5ad_path=h5ad_path,
        visium_path=visium_path,
        stereo_seq_path=stereo_seq_path,
        file_names=file_names,
    )
    result["download_dir"] = str(root)
    result["manifest"] = manifest
    result["readiness"] = readiness_bundle.get("readiness", result.get("readiness"))
    result["readiness_score"] = readiness_bundle["readiness"].get("score", result.get("readiness_score", 0))
    result["compatibility"] = readiness_bundle.get("compatibility", result.get("compatibility"))
    result["source"] = result.get("source") or "download_manifest"
    if result.get("adata") is None:
        result.setdefault("warnings", []).extend([
            "Downloaded files detected but full loader not yet available for this platform.",
            "Partial preview and readiness assessment are still available.",
        ])
    return normalize_loader_result(result)


def save_upload_to_temp(uploaded_file, suffix: str) -> Path:
    """Write Streamlit UploadedFile to temp path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded_file.getbuffer())
        return Path(f.name)
