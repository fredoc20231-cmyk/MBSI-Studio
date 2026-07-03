"""Akoya CODEX / PhenoCycler multiplexed-protein ingestion — real loader.

CODEX produces a single-cell protein *intensity* table (not counts): one row
per cell, marker columns plus centroid columns (``x``/``y`` or
``X_cent``/``Y_cent``). We load it into AnnData where ``X`` holds mean marker
intensities and ``obsm['spatial']`` holds the centroids. Non-marker columns
(area, size, DAPI, region) are carried into ``obs``. An exported ``.h5ad`` is
accepted as a fallback.
"""

from __future__ import annotations

import gzip
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_h5ad
from mbsi.io.validators import compute_readiness

_TABLE_SUFFIX = ("cell_data.csv", "cell_intensities.csv", "codex.csv",
                 "cell_data.csv.gz", "quantification.csv")
# Columns that are metadata, not protein markers.
_META_COLS = {
    "cell_id", "cellid", "cell", "region", "regionid", "tile", "fov",
    "area", "size", "volume", "z", "zplane", "cluster", "celltype",
    "dapi", "hoechst", "blank", "empty",
}
_X_COLS = ("x", "x_cent", "x_centroid", "centroid_x", "cx", "xmin")
_Y_COLS = ("y", "y_cent", "y_centroid", "centroid_y", "cy", "ymin")


def _find_first(root: Path, suffixes: Tuple[str, ...]) -> Optional[Path]:
    lowered = tuple(s.lower() for s in suffixes)
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name.lower().endswith(lowered):
            return path
    return None


def _read_csv(path: Path) -> pd.DataFrame:
    if path.name.lower().endswith(".gz"):
        with gzip.open(path, "rt") as handle:
            return pd.read_csv(handle)
    return pd.read_csv(path)


def _resolve_bundle(path: Union[str, Path]) -> Tuple[Path, Optional[Path]]:
    path = Path(path)
    if path.is_dir():
        return path, None
    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_codex_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        return tmp, tmp
    if path.suffix.lower() in (".h5ad", ".csv", ".gz"):
        return path.parent, None
    raise FileNotFoundError(f"Not a CODEX bundle directory or ZIP: {path}")


def _pick(colmap: Dict[str, str], candidates: Tuple[str, ...]) -> Optional[str]:
    for cand in candidates:
        if cand in colmap:
            return colmap[cand]
    return None


def read_codex_table(path: Path) -> ad.AnnData:
    """Load a CODEX single-cell protein table into AnnData with ``obsm['spatial']``."""
    df = _read_csv(path)
    colmap = {c.lower(): c for c in df.columns}

    x_col = _pick(colmap, _X_COLS)
    y_col = _pick(colmap, _Y_COLS)
    if x_col is None or y_col is None:
        raise ValueError("CODEX table must include centroid x/y columns")

    id_col = _pick(colmap, ("cell_id", "cellid", "cell"))
    if id_col is not None:
        cell_ids = df[id_col].astype(str).values
    else:
        cell_ids = np.array([f"cell_{i}" for i in range(len(df))])

    # Marker columns = numeric columns that are not centroids/metadata.
    marker_cols: List[str] = []
    meta_cols: List[str] = []
    for c in df.columns:
        if c in (x_col, y_col):
            continue
        base = c.lower()
        if base in _META_COLS or (id_col is not None and c == id_col):
            meta_cols.append(c)
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            marker_cols.append(c)
        else:
            meta_cols.append(c)
    if not marker_cols:
        raise ValueError("No protein-marker intensity columns detected in CODEX table")

    intensities = df[marker_cols].astype(np.float32).values
    coords = df[[x_col, y_col]].astype(float).values.astype(np.float32)

    adata = ad.AnnData(X=intensities)
    adata.obs_names = cell_ids.astype(str)
    adata.var_names = [str(m) for m in marker_cols]
    adata.obsm["spatial"] = coords
    adata.obs["x"] = coords[:, 0]
    adata.obs["y"] = coords[:, 1]
    for c in meta_cols:
        adata.obs[c] = df[c].values
    # Protein panel: use summed intensity as a QC proxy for "total signal".
    adata.obs["total_counts"] = intensities.sum(axis=1)
    adata.uns["codex"] = {
        "table_path": str(path),
        "modality": "protein_intensity",
        "n_markers": len(marker_cols),
        "markers": [str(m) for m in marker_cols],
        "vendor": "akoya_codex",
    }
    return adata


def load_codex(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load CODEX table (dir/ZIP/CSV) or exported h5ad; return AnnData + meta."""
    path = Path(path)
    if path.suffix.lower() == ".h5ad":
        adata, meta = ingest_h5ad(path)
        meta["platform"] = "codex"
        return adata, meta

    bundle_root, tmp = _resolve_bundle(path)
    try:
        table = path if path.suffix.lower() == ".csv" else _find_first(bundle_root, _TABLE_SUFFIX)
        if table is None:
            h5ads = list(bundle_root.rglob("*.h5ad"))
            if h5ads:
                adata, meta = ingest_h5ad(h5ads[0])
                meta["platform"] = "codex"
                return adata, meta
            raise FileNotFoundError(f"No CODEX cell-intensity table under {bundle_root}")
        adata = read_codex_table(table)
        detection = detect_platform(bundle_root)
        detection["platform"] = "codex"
        detection["technology_key"] = "codex"
        detection["modality"] = "protein"
        detection["missing"] = [m for m in detection.get("missing", []) if "stub" not in m.lower()]
        adata = normalize_to_contract(adata, platform="codex", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "codex",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
            "codex": adata.uns.get("codex", {}),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
