"""Platform auto-detection from paths or uploaded file names."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List, Union

PlatformDetection = Dict[str, Any]

VISIUM_REQUIRED = [
    "filtered_feature_bc_matrix.h5",
    "filtered_feature_bc_matrix/matrix.mtx",
]
VISIUM_POSITIONS = [
    "spatial/tissue_positions.csv",
    "spatial/tissue_positions_list.csv",
]
VISIUM_OPTIONAL = [
    "spatial/scalefactors_json.json",
    "spatial/tissue_hires_image.png",
    "spatial/tissue_lowres_image.png",
]

XENIUM_MARKERS = [
    "cell_feature_matrix",
    "cells.csv",
    "cells.parquet",
]


def _normalize_inputs(path_or_files: Union[str, Path, List[str], Dict[str, Any]]) -> tuple[Path | None, List[str]]:
    if isinstance(path_or_files, dict):
        names = list(path_or_files.keys())
        root = path_or_files.get("_root")
        return (Path(root) if root else None, names)
    if isinstance(path_or_files, (str, Path)):
        p = Path(path_or_files)
        if p.is_dir():
            names = [str(f.relative_to(p)).replace("\\", "/") for f in p.rglob("*") if f.is_file()]
            return p, names
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as zf:
                names = zf.namelist()
            return p, names
        return p.parent, [p.name]
    names = [Path(f).name if not isinstance(f, str) or "/" not in f else f for f in path_or_files]
    return None, names


def _has_any(names: List[str], candidates: List[str]) -> bool:
    lowered = [n.lower().replace("\\", "/") for n in names]
    for c in candidates:
        c_low = c.lower()
        if any(c_low in n for n in lowered):
            return True
    return False


def detect_platform(path_or_files: Union[str, Path, List[str], Dict[str, Any]]) -> PlatformDetection:
    """Detect spatial omics platform from folder, zip, or file name list."""
    root, names = _normalize_inputs(path_or_files)
    required_found: List[str] = []
    optional_found: List[str] = []
    missing: List[str] = []

    has_matrix = _has_any(names, ["filtered_feature_bc_matrix.h5", "filtered_feature_bc_matrix/matrix.mtx", "matrix.mtx"])
    has_positions = _has_any(names, VISIUM_POSITIONS)
    has_scalefactors = _has_any(names, ["scalefactors_json.json"])
    has_h5ad = _has_any(names, [".h5ad"])
    has_csv_matrix = _has_any(names, ["matrix.csv", "counts.csv"]) or any(n.endswith(".csv") and "coord" not in n.lower() for n in names)
    has_coords = _has_any(names, ["coordinates.csv", "coords.csv", "spatial.csv"]) or any("coord" in n.lower() for n in names)
    has_xenium = _has_any(names, XENIUM_MARKERS)

    if has_matrix and has_positions:
        platform = "visium"
        if has_matrix:
            required_found.append("count_matrix")
        if has_positions:
            required_found.append("tissue_positions")
        else:
            missing.append("tissue_positions")
        if has_scalefactors:
            optional_found.append("scalefactors")
        confidence = 0.95 if has_scalefactors else 0.85
    elif has_xenium:
        platform = "xenium"
        required_found.append("xenium_bundle")
        missing.append("full_xenium_loader_phase2")
        confidence = 0.6
    elif has_h5ad:
        platform = "generic_h5ad"
        required_found.append("h5ad")
        confidence = 0.9
    elif has_csv_matrix and has_coords:
        platform = "csv_matrix"
        required_found.extend(["count_matrix_csv", "coordinates_csv"])
        confidence = 0.8
    elif has_h5ad or has_matrix or has_csv_matrix:
        platform = "incomplete"
        if has_matrix or has_csv_matrix:
            required_found.append("partial_matrix")
        missing.append("spatial_coordinates_or_positions")
        confidence = 0.4
    else:
        platform = "unknown"
        missing.append("recognized_spatial_omics_files")
        confidence = 0.0

    return {
        "platform": platform,
        "required_found": required_found,
        "optional_found": optional_found,
        "missing": missing,
        "confidence": confidence,
        "root": str(root) if root else None,
        "n_files": len(names),
    }
