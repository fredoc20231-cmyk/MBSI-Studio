"""Inspect downloaded files, detect platform, and assess ingestion readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.io.downloader.archive import is_archive, list_archive_contents
from mbsi.schema.technology import TECHNOLOGY_CATALOG, get_technology


def _collect_file_names(directory: Path) -> List[str]:
    names: List[str] = []
    if not directory.is_dir():
        return names
    for f in directory.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(directory)).replace("\\", "/")
            names.append(rel)
            if is_archive(f):
                names.extend(list_archive_contents(f))
    return names


def inspect_downloaded_files(download_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Inspect a download directory and detect spatial omics platform.

    Returns detection dict plus file inventory.
    """
    root = Path(download_dir)
    if not root.is_dir():
        return {
            "platform": "unknown",
            "confidence": 0.0,
            "files": [],
            "n_files": 0,
            "root": str(root),
            "error": "download directory not found",
        }

    local_files = _collect_file_names(root)
    detection = detect_platform({"_root": str(root), **{n: True for n in local_files}})
    detection["files"] = local_files
    detection["n_local_files"] = len([f for f in root.rglob("*") if f.is_file()])
    return detection


def build_required_file_checklist(platform: str, files: List[str]) -> Dict[str, Any]:
    """Build required vs found checklist for a detected platform."""
    spec = get_technology(platform) if platform in TECHNOLOGY_CATALOG else None
    required_labels = list(spec.required_files) if spec else []
    lowered = [f.lower().replace("\\", "/") for f in files]

    found: List[str] = []
    missing: List[str] = []

    for req in required_labels:
        req_low = req.lower()
        tokens = [t.strip() for t in req_low.replace(" or ", "|").split("|")]
        matched = any(
            any(tok in name for name in lowered)
            for tok in tokens
            if tok and tok not in ("optional", "recommended")
        )
        if matched:
            found.append(req)
        elif "optional" not in req_low and "recommended" not in req_low:
            missing.append(req)
        else:
            found.append(req)

    return {
        "platform": platform,
        "technology_label": spec.label if spec else platform,
        "required_files": required_labels,
        "found": found,
        "missing": missing,
        "n_files": len(files),
        "complete": len(missing) == 0 and bool(required_labels),
    }


def update_ingestion_readiness(
    download_dir: Union[str, Path],
    detection: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compute readiness score and module compatibility from downloaded files.

    Uses detect_platform + technology catalog + compatibility matrix (no AnnData yet).
    """
    root = Path(download_dir)
    detection = detection or inspect_downloaded_files(root)
    platform = detection.get("platform", "unknown")
    files = detection.get("files", [])
    checklist = build_required_file_checklist(platform, files)

    confidence = float(detection.get("confidence", 0.0))
    n_found = len(detection.get("required_found", []))
    n_missing = len(detection.get("missing", []))

    if platform == "unknown":
        score = 0
        status = "unknown_platform"
    elif platform == "incomplete":
        score = int(min(40, confidence * 50))
        status = "incomplete_dataset"
    else:
        base = int(confidence * 70)
        bonus = min(30, n_found * 10)
        penalty = min(40, n_missing * 15)
        score = max(0, min(100, base + bonus - penalty))
        status = "ready" if score >= 60 and not checklist.get("missing") else "partial"

    readiness = {
        "status": status,
        "score": score,
        "platform": platform,
        "confidence": confidence,
        "checklist": checklist,
        "required_found": detection.get("required_found", []),
        "missing": detection.get("missing", []),
        "partial_support": detection.get("partial_support", False),
    }

    compatibility = get_compatibility_matrix(None, detection, technology_key=platform)

    return {
        "readiness": readiness,
        "compatibility": compatibility,
        "detection": detection,
        "checklist": checklist,
    }
