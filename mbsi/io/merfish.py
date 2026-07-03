"""Vizgen MERSCOPE / MERFISH ingestion — real bundle loader.

Parses the standard MERSCOPE cell-level output:
  * ``cell_by_gene.csv``      — cells x genes count matrix (row index = cell id)
  * ``cell_metadata.csv``     — per-cell centroids (``center_x``/``center_y``)
Files may carry a run prefix (e.g. ``<run>_cell_by_gene.csv``) and may be
gzip-compressed or parquet. An exported ``.h5ad`` (with ``obsm['spatial']``)
is accepted as a fallback.
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

_CELL_BY_GENE = ("cell_by_gene.csv", "cell_by_gene.csv.gz", "cell_by_gene.parquet")
_CELL_META = ("cell_metadata.csv", "cell_metadata.csv.gz", "cell_metadata.parquet")


def _find_first(root: Path, suffixes: Tuple[str, ...]) -> Optional[Path]:
    """Find a file whose name ends with any of ``suffixes`` (case-insensitive)."""
    lowered = tuple(s.lower() for s in suffixes)
    # exact names first
    for name in suffixes:
        direct = root / name
        if direct.is_file():
            return direct
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name.lower().endswith(lowered):
            return path
    return None


def _read_table(path: Path) -> pd.DataFrame:
    name = path.name.lower()
    if name.endswith(".parquet"):
        return pd.read_parquet(path)
    if name.endswith(".gz"):
        with gzip.open(path, "rt") as handle:
            return pd.read_csv(handle, index_col=0)
    return pd.read_csv(path, index_col=0)


def _resolve_bundle(path: Union[str, Path]) -> Tuple[Path, Optional[Path]]:
    path = Path(path)
    if path.is_dir():
        return path, None
    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_merfish_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        return tmp, tmp
    if path.suffix.lower() in (".h5ad", ".csv", ".gz", ".parquet"):
        return path.parent, None
    raise FileNotFoundError(f"Not a MERSCOPE bundle directory or ZIP: {path}")


def read_merscope_bundle(root: Path) -> ad.AnnData:
    """Load a MERSCOPE bundle into cell-level AnnData with ``obsm['spatial']``."""
    matrix_path = _find_first(root, _CELL_BY_GENE)
    meta_path = _find_first(root, _CELL_META)
    if matrix_path is None:
        raise FileNotFoundError(f"No cell_by_gene matrix under {root}")

    counts = _read_table(matrix_path)
    counts.index = counts.index.astype(str)

    # Vizgen matrices include control probes ("Blank-*"); keep them but flag.
    blank_mask = counts.columns.str.lower().str.startswith(("blank", "blank-"))

    if meta_path is not None:
        meta = _read_table(meta_path)
        meta.index = meta.index.astype(str)
        x_col = next((c for c in ("center_x", "center_x_um", "x", "X") if c in meta.columns), None)
        y_col = next((c for c in ("center_y", "center_y_um", "y", "Y") if c in meta.columns), None)
        if x_col is None or y_col is None:
            raise ValueError("cell_metadata must include center_x/center_y (or x/y) columns")
        common = counts.index.intersection(meta.index)
        if common.empty:
            raise ValueError("No overlapping cell IDs between matrix and metadata")
        counts = counts.loc[common]
        meta = meta.loc[common]
        coords = meta[[x_col, y_col]].astype(float).values.astype(np.float32)
    else:
        # Fallback: centroids embedded as x/y columns in the matrix file.
        x_col = next((c for c in ("center_x", "x", "X") if c in counts.columns), None)
        y_col = next((c for c in ("center_y", "y", "Y") if c in counts.columns), None)
        if x_col is None or y_col is None:
            raise FileNotFoundError(f"No cell_metadata (centroids) found under {root}")
        coords = counts[[x_col, y_col]].astype(float).values.astype(np.float32)
        counts = counts.drop(columns=[x_col, y_col])
        blank_mask = counts.columns.str.lower().str.startswith(("blank", "blank-"))
        meta = pd.DataFrame(index=counts.index)

    adata = ad.AnnData(X=counts.values.astype(np.float32))
    adata.obs_names = counts.index.astype(str)
    adata.var_names = counts.columns.astype(str)
    adata.obsm["spatial"] = coords
    adata.obs["center_x"] = coords[:, 0]
    adata.obs["center_y"] = coords[:, 1]
    adata.var["control_probe"] = np.asarray(blank_mask)
    for col in meta.columns:
        if col not in (x_col, y_col):
            adata.obs[col] = meta[col].values
    adata.obs["total_counts"] = np.asarray(adata.X.sum(axis=1)).ravel()
    adata.uns["merfish"] = {
        "matrix_path": str(matrix_path),
        "metadata_path": str(meta_path) if meta_path else None,
        "n_control_probes": int(blank_mask.sum()),
        "vendor": "vizgen_merscope",
    }
    return adata


def load_merfish(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load MERSCOPE/MERFISH bundle (dir/ZIP) or exported h5ad; return AnnData + meta."""
    path = Path(path)
    if path.suffix.lower() == ".h5ad":
        adata, meta = ingest_h5ad(path)
        meta["platform"] = "merfish"
        return adata, meta

    bundle_root, tmp = _resolve_bundle(path)
    try:
        # If the bundle only contains an exported h5ad, use it.
        if _find_first(bundle_root, _CELL_BY_GENE) is None:
            h5ads = list(bundle_root.rglob("*.h5ad"))
            if h5ads:
                adata, meta = ingest_h5ad(h5ads[0])
                meta["platform"] = "merfish"
                return adata, meta
        adata = read_merscope_bundle(bundle_root)
        detection = detect_platform(bundle_root)
        detection["platform"] = "merfish"
        detection["technology_key"] = "merfish"
        detection["missing"] = [m for m in detection.get("missing", []) if "stub" not in m.lower()]
        adata = normalize_to_contract(adata, platform="merfish", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "merfish",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
            "merfish": adata.uns.get("merfish", {}),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
