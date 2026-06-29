"""Lightweight patch preview while dataset is still downloading."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from mbsi.io.downloader.archive import is_archive, list_archive_contents
from mbsi.io.downloader.inspector import inspect_downloaded_files
from mbsi.io.downloader.manifest import DownloadManifest

PARTIAL_MESSAGE = "Partial preview only — full analysis requires complete dataset."


def select_preview_patch(
    download_dir: Union[str, Path],
    *,
    strategy: str = "center_or_first",
) -> Dict[str, Any]:
    """
    Select a spatial patch or file subset for preview.

    strategy: center_or_first — prefer coordinates CSV center crop, else first image.
    """
    root = Path(download_dir)
    result: Dict[str, Any] = {"strategy": strategy, "patch_type": None, "source_file": None}

    coord_candidates: List[Path] = []
    image_candidates: List[Path] = []

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        low = f.name.lower()
        if any(k in low for k in ("coord", "position", "cells.csv", "keypoints")):
            if f.suffix.lower() in (".csv", ".parquet"):
                coord_candidates.append(f)
        if low.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")) or "he_image" in low:
            image_candidates.append(f)

    if strategy == "center_or_first":
        if coord_candidates:
            src = sorted(coord_candidates, key=lambda p: p.name)[0]
            result["patch_type"] = "coordinates"
            result["source_file"] = str(src.relative_to(root))
            try:
                df = pd.read_csv(src, nrows=5000)
                x_col = next((c for c in df.columns if c.lower() in ("x", "x_centroid", "x_location")), None)
                y_col = next((c for c in df.columns if c.lower() in ("y", "y_centroid", "y_location")), None)
                if x_col and y_col:
                    xs = df[x_col].astype(float)
                    ys = df[y_col].astype(float)
                    cx, cy = xs.median(), ys.median()
                    dist = (xs - cx) ** 2 + (ys - cy) ** 2
                    idx = dist.nsmallest(min(500, len(dist))).index
                    result["patch_coords"] = {
                        "x": xs.loc[idx].tolist(),
                        "y": ys.loc[idx].tolist(),
                        "n_points": len(idx),
                    }
            except Exception as exc:
                result["error"] = str(exc)
            return result

        if image_candidates:
            src = sorted(image_candidates, key=lambda p: p.name)[0]
            result["patch_type"] = "image"
            result["source_file"] = str(src.relative_to(root))
            return result

    result["patch_type"] = "none"
    return result


def _thumbnail_from_image(path: Path, max_size: int = 128) -> Optional[str]:
    try:
        from PIL import Image

        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((max_size, max_size))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None


def _expression_preview(root: Path) -> Dict[str, Any]:
    """Attempt a tiny expression preview from CSV matrix if present."""
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        low = f.name.lower()
        if low.endswith(".csv") and any(k in low for k in ("matrix", "counts", "expr", "gene")):
            try:
                df = pd.read_csv(f, nrows=20, index_col=0)
                if df.shape[1] >= 2:
                    return {
                        "source": str(f.relative_to(root)),
                        "n_genes_preview": df.shape[0],
                        "n_cells_preview": df.shape[1],
                        "mean_counts": float(np.nanmean(df.values.astype(float))),
                    }
            except Exception:
                continue
    return {}


def run_patch_preview_analysis(
    download_dir: Union[str, Path],
    detection: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run lightweight preview: thumbnail, tissue hint, coord scatter data,
    expression preview, completeness, tech confidence.
    """
    root = Path(download_dir)
    detection = detection or inspect_downloaded_files(root)
    patch = select_preview_patch(root)

    preview: Dict[str, Any] = {
        "partial": True,
        "message": PARTIAL_MESSAGE,
        "platform": detection.get("platform", "unknown"),
        "confidence": detection.get("confidence", 0.0),
        "n_files": detection.get("n_local_files", detection.get("n_files", 0)),
        "patch": patch,
        "tissue_hint": None,
        "expression_preview": _expression_preview(root),
        "completeness": {
            "required_found": detection.get("required_found", []),
            "missing": detection.get("missing", []),
        },
    }

    if patch.get("patch_type") == "image" and patch.get("source_file"):
        img_path = root / patch["source_file"]
        thumb = _thumbnail_from_image(img_path)
        if thumb:
            preview["thumbnail_b64"] = thumb
            preview["tissue_hint"] = "Histology image available — tissue morphology preview possible"

    if patch.get("patch_coords"):
        preview["coord_scatter"] = patch["patch_coords"]
        preview["tissue_hint"] = preview["tissue_hint"] or "Spatial coordinates detected — patch scatter available"

    if detection.get("optional_found"):
        if any("image" in str(x).lower() or "histology" in str(x).lower() for x in detection["optional_found"]):
            preview["tissue_hint"] = preview["tissue_hint"] or "Registered histology referenced in bundle"

    return preview


def run_incremental_patch_analysis(job_manifest: Union[DownloadManifest, Dict[str, Any]]) -> Dict[str, Any]:
    """Update preview as files arrive during an active download job."""
    if isinstance(job_manifest, DownloadManifest):
        manifest = job_manifest
        output_dir = manifest.output_dir
        completed = [u for u in manifest.urls if u.status == "complete"]
    else:
        output_dir = job_manifest.get("output_dir", "")
        completed = [u for u in job_manifest.get("urls", []) if u.get("status") == "complete"]

    if not output_dir:
        return {"partial": True, "message": PARTIAL_MESSAGE, "n_complete": 0}

    detection = inspect_downloaded_files(output_dir)
    preview = run_patch_preview_analysis(output_dir, detection)
    preview["n_complete"] = len(completed)
    preview["n_total"] = len(job_manifest.urls) if isinstance(job_manifest, DownloadManifest) else len(job_manifest.get("urls", []))
    preview["job_status"] = manifest.status if isinstance(job_manifest, DownloadManifest) else job_manifest.get("status")
    preview["files_complete"] = [
        u.filename if isinstance(u, object) and hasattr(u, "filename") else u.get("filename")
        for u in completed
    ]
    return preview
