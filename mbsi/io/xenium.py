"""10x Xenium ingestion — Milestone 1 real bundle loader."""

from __future__ import annotations

import gzip
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, csr_matrix

from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import detect_platform
from mbsi.io.validators import compute_readiness

_CELL_TABLE_NAMES = (
    "cells.csv.gz",
    "cells.csv",
    "cells.parquet",
)
_MATRIX_NAMES = ("cell_feature_matrix.h5",)
_OPTIONAL_ARTIFACTS = {
    "transcripts": ("transcripts.parquet", "transcripts.csv.gz"),
    "boundaries": ("cell_boundaries.parquet", "cell_boundaries.csv.gz"),
    "morphology": ("morphology.ome.tif", "morphology.ome.tiff", "morphology_focus.ome.tif"),
}


def _find_first(root: Path, names: Tuple[str, ...]) -> Optional[Path]:
    for name in names:
        direct = root / name
        if direct.is_file():
            return direct
    lowered = {n.lower(): n for n in names}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        base = path.name.lower()
        if base in lowered:
            return path
    return None


def _resolve_bundle(path: Union[str, Path]) -> tuple[Path, Path | None]:
    """Return Xenium bundle root and optional temp dir to clean up."""
    path = Path(path)
    if path.is_dir():
        if _find_first(path, _MATRIX_NAMES) or _find_first(path, _CELL_TABLE_NAMES):
            return path, None
        for sub in ("outs", "xenium", "output", "output-xenium"):
            candidate = path / sub
            if candidate.is_dir():
                return candidate, None
        return path, None

    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_xenium_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        detection = detect_platform(tmp)
        root = Path(detection["root"]) if detection.get("root") else tmp
        for candidate in [root, tmp]:
            if _find_first(candidate, _MATRIX_NAMES) or _find_first(candidate, _CELL_TABLE_NAMES):
                return candidate, tmp
        for matrix in tmp.rglob("cell_feature_matrix.h5"):
            return matrix.parent, tmp
        return tmp, tmp

    raise FileNotFoundError(f"Not a Xenium bundle directory or ZIP: {path}")


def _load_cell_matrix(h5_path: Path) -> tuple[csr_matrix, List[str], List[str]]:
    """Load 10x-style cell_feature_matrix.h5 (cells × genes)."""
    with h5py.File(h5_path, "r") as f:
        mat = f["matrix"]
        data = mat["data"][:]
        indices = mat["indices"][:]
        indptr = mat["indptr"][:]
        shape = tuple(mat["shape"][:])
        X = csc_matrix((data, indices, indptr), shape=shape).T
        genes = [
            g.decode() if isinstance(g, bytes) else str(g)
            for g in mat["features"]["name"][:]
        ]
        barcodes = [
            b.decode() if isinstance(b, bytes) else str(b)
            for b in mat["barcodes"][:]
        ]
    return X, genes, barcodes


def _load_cells_table(path: Path) -> pd.DataFrame:
    """Load Xenium cells metadata table."""
    if path.suffix == ".gz" or path.name.endswith(".csv.gz"):
        with gzip.open(path, "rt") as handle:
            df = pd.read_csv(handle)
    elif path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    return df


def _spatial_from_cells(cells: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Extract spatial coordinates keyed by cell id."""
    id_col = None
    for candidate in ("cell_id", "barcode", "Cell_ID", "cell"):
        if candidate in cells.columns:
            id_col = candidate
            break
    if id_col is None:
        id_col = cells.columns[0]

    x_col = next((c for c in ("x_centroid", "x", "X") if c in cells.columns), None)
    y_col = next((c for c in ("y_centroid", "y", "Y") if c in cells.columns), None)
    if x_col is None or y_col is None:
        raise ValueError("Cells table must include x_centroid/y_centroid (or x/y) columns")

    cells = cells.copy()
    cells[id_col] = cells[id_col].astype(str)
    cells = cells.set_index(id_col)
    coords = cells[[x_col, y_col]].astype(float).values.astype(np.float32)
    return cells, coords


def _collect_optional_artifacts(root: Path) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for key, names in _OPTIONAL_ARTIFACTS.items():
        path = _find_first(root, names)
        if path is not None:
            found[key] = str(path)
    return found


def read_xenium_bundle(root: Union[str, Path]) -> ad.AnnData:
    """Load Xenium bundle into cell-level AnnData with obsm['spatial']."""
    root = Path(root)
    matrix_path = _find_first(root, _MATRIX_NAMES)
    if matrix_path is None:
        raise FileNotFoundError(f"No cell_feature_matrix.h5 under {root}")

    cells_path = _find_first(root, _CELL_TABLE_NAMES)
    if cells_path is None:
        raise FileNotFoundError(f"No cells.csv.gz / cells.parquet under {root}")

    X, genes, barcodes = _load_cell_matrix(matrix_path)
    cells_raw = _load_cells_table(cells_path)
    id_col = next((c for c in ("cell_id", "barcode", "Cell_ID", "cell") if c in cells_raw.columns), cells_raw.columns[0])
    x_col = next((c for c in ("x_centroid", "x", "X") if c in cells_raw.columns), None)
    y_col = next((c for c in ("y_centroid", "y", "Y") if c in cells_raw.columns), None)
    if x_col is None or y_col is None:
        raise ValueError("Cells table must include x_centroid/y_centroid (or x/y) columns")

    cells_df = cells_raw.copy()
    cells_df[id_col] = cells_df[id_col].astype(str).str.strip()
    cells_df = cells_df.set_index(id_col)
    barcodes = [str(b).strip() for b in barcodes]

    common = [b for b in barcodes if b in cells_df.index]
    if not common:
        cells_df.index = cells_df.index.str.strip()
        common = [b for b in barcodes if b in cells_df.index]
    if not common:
        raise ValueError("No overlapping cell IDs between matrix barcodes and cells table")

    idx = [barcodes.index(b) for b in common]
    X = X[idx, :]
    barcodes = common
    cells_df = cells_df.loc[barcodes]
    coords = cells_df[[x_col, y_col]].astype(float).values.astype(np.float32)

    adata = ad.AnnData(X=X)
    adata.var_names = genes
    adata.obs_names = barcodes
    adata.obsm["spatial"] = coords
    adata.obs["x_centroid"] = cells_df[x_col].astype(float).values
    adata.obs["y_centroid"] = cells_df[y_col].astype(float).values

    for col in cells_df.columns:
        if col not in (x_col, y_col):
            adata.obs[col] = cells_df[col].values

    optional = _collect_optional_artifacts(root)
    adata.uns["xenium"] = {
        "matrix_path": str(matrix_path),
        "cells_path": str(cells_path),
        "optional_artifacts": optional,
    }
    if "transcript_counts" in adata.obs.columns:
        adata.obs["total_counts"] = pd.to_numeric(adata.obs["transcript_counts"], errors="coerce").fillna(0)
    return adata


def load_xenium(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load Xenium bundle from directory or ZIP; return AnnData + metadata."""
    bundle_root, tmp = _resolve_bundle(path)
    try:
        adata = read_xenium_bundle(bundle_root)
        detection = detect_platform(bundle_root)
        detection["platform"] = "xenium"
        detection["technology_key"] = "xenium"
        if detection.get("missing"):
            detection["missing"] = [m for m in detection["missing"] if "phase2" not in m.lower()]
        if adata.uns.get("xenium", {}).get("optional_artifacts"):
            detection.setdefault("optional_found", []).extend(
                list(adata.uns["xenium"]["optional_artifacts"].keys())
            )
        adata = normalize_to_contract(adata, platform="xenium", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "xenium",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
            "xenium": adata.uns.get("xenium", {}),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
