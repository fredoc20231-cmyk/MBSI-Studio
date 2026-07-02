"""Platform auto-detection from paths or uploaded file names."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, List, Union

from mbsi.schema.technology import TECHNOLOGY_CATALOG

PlatformDetection = Dict[str, Any]

VISIUM_POSITIONS = [
    "spatial/tissue_positions.csv",
    "spatial/tissue_positions_list.csv",
]

XENIUM_MARKERS = [
    "cell_feature_matrix",
    "cells.csv",
    "cells.parquet",
]

COSMX_MARKERS = [
    "exprmat",
    "_exprmat_file.csv",
    "fov_positions",
    "metadata_file.csv",
]

MERFISH_MARKERS = [
    "merfish",
    "merscope",
    "vizgen",
    "cell_by_gene",
]

STEREO_SEQ_MARKERS = [
    ".gef",
    ".cgef",
    "stereomap",
    "saw",
    "stereo-seq",
    "stomics",
    "bin100",
]

CODEX_MARKERS = [
    "codex",
    "cell_intensities",
    "cell_data.csv",
    "multiplex",
]

SPATIAL_ATAC_MARKERS = [
    "spatial_atac",
    "atac_peaks",
    "fragments.tsv",
    "peaks.bed",
    "gene_activity",
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


def _has_suffix(names: List[str], suffixes: List[str]) -> bool:
    lowered = [n.lower() for n in names]
    return any(any(n.endswith(s) for s in suffixes) for n in lowered)


def detect_platform(path_or_files: Union[str, Path, List[str], Dict[str, Any]]) -> PlatformDetection:
    """Detect spatial omics platform from folder, zip, or file name list."""
    root, names = _normalize_inputs(path_or_files)
    required_found: List[str] = []
    optional_found: List[str] = []
    missing: List[str] = []

    has_visium_matrix = _has_any(
        names,
        ["filtered_feature_bc_matrix.h5", "filtered_feature_bc_matrix/matrix.mtx", "matrix.mtx"],
    )
    has_visium_hd = _has_any(names, ["binned_outputs", "square_008um", "visium_hd", "008um"])
    has_positions = _has_any(names, VISIUM_POSITIONS + ["tissue_positions.parquet"])
    has_scalefactors = _has_any(names, ["scalefactors_json.json"])
    has_h5ad = _has_suffix(names, [".h5ad"])
    has_csv_matrix = _has_any(names, ["matrix.csv", "counts.csv"]) or any(
        n.endswith(".csv") and "coord" not in n.lower() and "exprmat" not in n.lower() for n in names
    )
    has_coords = _has_any(names, ["coordinates.csv", "coords.csv", "spatial.csv"]) or any(
        "coord" in n.lower() for n in names
    )
    has_xenium_matrix = _has_any(names, ["cell_feature_matrix"])
    has_xenium_cells = _has_any(names, ["cells.csv", "cells.parquet", "cells.csv.gz"])
    has_xenium = has_xenium_matrix and has_xenium_cells
    has_cosmx = _has_any(names, COSMX_MARKERS)
    has_merfish = _has_any(names, MERFISH_MARKERS)
    has_stereo = _has_suffix(names, [".gef", ".cgef"]) or _has_any(names, STEREO_SEQ_MARKERS)
    has_codex = _has_any(names, CODEX_MARKERS)
    has_spatial_atac = _has_any(names, SPATIAL_ATAC_MARKERS)

    platform = "unknown"
    confidence = 0.0

    if has_stereo:
        platform = "stereo_seq"
        if _has_suffix(names, [".gef"]):
            required_found.append("gef_matrix")
        if _has_suffix(names, [".cgef"]):
            required_found.append("cgef_matrix")
        if _has_any(names, ["stereomap", "saw"]):
            optional_found.append("saw_stereomap_workflow")
        if _has_any(names, [".html"]) and _has_any(names, ["qc", "report"]):
            optional_found.append("html_qc_report")
        if _has_any(names, ["segmentation", "mask", "cell_mask"]):
            optional_found.append("segmentation")
        if _has_any(names, ["he.", "h&e", "mif", ".tif", ".tiff", ".png"]):
            optional_found.append("registered_images")
        if not _has_suffix(names, [".gef", ".cgef"]):
            missing.append("gef_or_cgef_expression_matrix")
        confidence = 0.85 if _has_suffix(names, [".gef", ".cgef"]) else 0.55
    elif has_visium_hd and (has_visium_matrix or has_positions):
        platform = "visium_hd"
        required_found.extend(["hd_binned_outputs", "tissue_positions"])
        if has_scalefactors:
            optional_found.append("scalefactors")
        confidence = 0.9
    elif has_visium_matrix and has_positions:
        platform = "visium"
        required_found.extend(["count_matrix", "tissue_positions"])
        if has_scalefactors:
            optional_found.append("scalefactors")
        confidence = 0.95 if has_scalefactors else 0.85
    elif has_xenium:
        platform = "xenium"
        required_found.extend(["cell_feature_matrix", "cells_table"])
        if _has_any(names, ["transcripts.parquet"]):
            optional_found.append("transcripts")
        if _has_any(names, ["cell_boundaries.parquet", "cell_boundaries.csv"]):
            optional_found.append("cell_boundaries")
        if _has_any(names, ["morphology.ome.tif", "morphology.ome.tiff"]):
            optional_found.append("morphology")
        confidence = 0.95 if has_xenium_matrix and has_xenium_cells else 0.7
    elif has_cosmx:
        platform = "cosmx"
        required_found.append("cosmx_expr_matrix")
        missing.append("full_cosmx_loader_stub")
        confidence = 0.55
    elif has_merfish:
        platform = "merfish"
        required_found.append("merfish_counts")
        missing.append("full_merfish_loader_stub")
        confidence = 0.5
    elif has_codex:
        platform = "codex"
        required_found.append("codex_intensity_matrix")
        missing.append("full_codex_loader_stub")
        confidence = 0.5
    elif has_spatial_atac:
        platform = "spatial_atac"
        required_found.append("spatial_atac_peaks")
        missing.append("full_spatial_atac_loader_stub")
        confidence = 0.55
    elif has_h5ad:
        platform = "generic_h5ad"
        required_found.append("h5ad")
        confidence = 0.9
    elif has_csv_matrix and has_coords:
        platform = "generic_h5ad"
        required_found.extend(["count_matrix_csv", "coordinates_csv"])
        confidence = 0.8
    elif has_h5ad or has_visium_matrix or has_csv_matrix:
        platform = "incomplete"
        if has_visium_matrix or has_csv_matrix:
            required_found.append("partial_matrix")
        missing.append("spatial_coordinates_or_positions")
        confidence = 0.4
    else:
        missing.append("recognized_spatial_omics_files")
        confidence = 0.0

    tech_spec = TECHNOLOGY_CATALOG.get(platform)
    return {
        "platform": platform,
        "technology_key": platform,
        "required_found": required_found,
        "optional_found": optional_found,
        "missing": missing,
        "confidence": confidence,
        "root": str(root) if root else None,
        "n_files": len(names),
        "technology_label": tech_spec.label if tech_spec else platform,
        "partial_support": platform in ("cosmx", "merfish", "codex", "spatial_atac", "stereo_seq", "visium_hd"),
    }
