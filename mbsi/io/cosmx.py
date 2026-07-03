"""NanoString CosMx SMI ingestion — real flat-file loader.

Parses the standard CosMx exported flat files:
  * ``*_exprMat_file.csv``   — long/wide expression keyed by ``fov`` + ``cell_ID``
  * ``*_metadata_file.csv``  — per-cell centroids (``CenterX_global_px`` / ``CenterY_global_px``)
Cell identity is ``(fov, cell_ID)``; ``cell_ID == 0`` is the FOV background and
is dropped. Negative-control probes (``NegPrb*`` / ``Negative*``) are flagged.
An exported ``.h5ad`` is accepted as a fallback.
"""

from __future__ import annotations

import gzip
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_h5ad
from mbsi.io.validators import compute_readiness

_EXPR_SUFFIX = ("exprmat_file.csv", "exprmat_file.csv.gz", "exprmat.csv")
_META_SUFFIX = ("metadata_file.csv", "metadata_file.csv.gz", "metadata.csv")
_ID_COLS = ("fov", "cell_ID", "cell_id")


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
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_cosmx_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        return tmp, tmp
    if path.suffix.lower() in (".h5ad", ".csv", ".gz"):
        return path.parent, None
    raise FileNotFoundError(f"Not a CosMx bundle directory or ZIP: {path}")


def _composite_id(df: pd.DataFrame) -> pd.Index:
    fov = df["fov"].astype(int).astype(str) if "fov" in df.columns else pd.Series("1", index=df.index)
    cid_col = "cell_ID" if "cell_ID" in df.columns else "cell_id"
    cid = df[cid_col].astype(int).astype(str)
    return pd.Index("c_" + fov.values + "_" + cid.values)


def read_cosmx_bundle(root: Path) -> ad.AnnData:
    """Load a CosMx flat-file bundle into cell-level AnnData with ``obsm['spatial']``."""
    expr_path = _find_first(root, _EXPR_SUFFIX)
    meta_path = _find_first(root, _META_SUFFIX)
    if expr_path is None:
        raise FileNotFoundError(f"No *_exprMat_file.csv under {root}")
    if meta_path is None:
        raise FileNotFoundError(f"No *_metadata_file.csv under {root}")

    expr = _read_csv(expr_path)
    meta = _read_csv(meta_path)

    gene_cols = [c for c in expr.columns if c not in _ID_COLS]
    cid_col = "cell_ID" if "cell_ID" in expr.columns else "cell_id"
    # Drop FOV background (cell_ID == 0).
    if cid_col in expr.columns:
        expr = expr[expr[cid_col].astype(int) != 0].copy()
    expr.index = _composite_id(expr)

    x_col = next((c for c in ("CenterX_global_px", "CenterX_global", "CenterX_local_px", "x", "CenterX") if c in meta.columns), None)
    y_col = next((c for c in ("CenterY_global_px", "CenterY_global", "CenterY_local_px", "y", "CenterY") if c in meta.columns), None)
    if x_col is None or y_col is None:
        raise ValueError("metadata must include CenterX_global_px/CenterY_global_px (or x/y)")
    if cid_col in meta.columns:
        meta = meta[meta[cid_col].astype(int) != 0].copy()
    meta.index = _composite_id(meta)

    common = expr.index.intersection(meta.index)
    if common.empty:
        raise ValueError("No overlapping (fov, cell_ID) between expression and metadata")
    expr = expr.loc[common]
    meta = meta.loc[common]

    counts = expr[gene_cols]
    control_mask = counts.columns.str.lower().str.startswith(("negprb", "negative", "falsecode", "syscontrol"))
    coords = meta[[x_col, y_col]].astype(float).values.astype(np.float32)

    adata = ad.AnnData(X=counts.values.astype(np.float32))
    adata.obs_names = counts.index.astype(str)
    adata.var_names = counts.columns.astype(str)
    adata.obsm["spatial"] = coords
    adata.obs["CenterX_global_px"] = coords[:, 0]
    adata.obs["CenterY_global_px"] = coords[:, 1]
    if "fov" in meta.columns:
        adata.obs["fov"] = meta["fov"].values
    adata.var["control_probe"] = np.asarray(control_mask)
    for col in meta.columns:
        if col not in (x_col, y_col, "fov") and col not in _ID_COLS:
            adata.obs[col] = meta[col].values
    adata.obs["total_counts"] = np.asarray(adata.X.sum(axis=1)).ravel()
    adata.uns["cosmx"] = {
        "expr_path": str(expr_path),
        "metadata_path": str(meta_path),
        "n_control_probes": int(control_mask.sum()),
        "vendor": "nanostring_cosmx",
    }
    return adata


def load_cosmx(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load CosMx flat-file bundle (dir/ZIP) or exported h5ad; return AnnData + meta."""
    path = Path(path)
    if path.suffix.lower() == ".h5ad":
        adata, meta = ingest_h5ad(path)
        meta["platform"] = "cosmx"
        return adata, meta

    bundle_root, tmp = _resolve_bundle(path)
    try:
        if _find_first(bundle_root, _EXPR_SUFFIX) is None:
            h5ads = list(bundle_root.rglob("*.h5ad"))
            if h5ads:
                adata, meta = ingest_h5ad(h5ads[0])
                meta["platform"] = "cosmx"
                return adata, meta
        adata = read_cosmx_bundle(bundle_root)
        detection = detect_platform(bundle_root)
        detection["platform"] = "cosmx"
        detection["technology_key"] = "cosmx"
        detection["missing"] = [m for m in detection.get("missing", []) if "stub" not in m.lower()]
        adata = normalize_to_contract(adata, platform="cosmx", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "cosmx",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
            "cosmx": adata.uns.get("cosmx", {}),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
