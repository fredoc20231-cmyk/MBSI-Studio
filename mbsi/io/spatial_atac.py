"""Spatial-ATAC ingestion — real loader for exported matrices.

Spatial-ATAC-seq (and spatial CUT&Tag) produce a peak- or gene-activity
matrix over spatial barcodes. We support, in priority order:

  1. An exported ``.h5ad`` with ``obsm['spatial']`` (already contract-ready).
  2. A 10x-style ``.h5`` matrix (peaks/gene-activity) + a Visium-style
     ``tissue_positions*.csv`` giving per-barcode coordinates.
  3. An MTX triplet (``matrix.mtx`` + ``features``/``peaks`` + ``barcodes``)
     alongside a positions file.

Fragment/BAM-level parsing is intentionally out of scope: those are converted
to a peak or gene-activity matrix upstream (ArchR / SnapATAC / Signac), which
is the correct granularity for spatial analysis.
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

_POSITION_NAMES = (
    "tissue_positions.csv", "tissue_positions_list.csv",
    "spatial/tissue_positions.csv", "spatial/tissue_positions_list.csv",
    "barcodes_pos.csv", "spatial.csv",
)


def _find_first(root: Path, names: Tuple[str, ...]) -> Optional[Path]:
    lowered = tuple(n.lower() for n in names)
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name.lower().endswith(lowered):
            return path
    return None


def _resolve_bundle(path: Union[str, Path]) -> Tuple[Path, Optional[Path]]:
    path = Path(path)
    if path.is_dir():
        return path, None
    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_atac_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        return tmp, tmp
    return path.parent, None


def _read_positions(path: Path) -> pd.DataFrame:
    """Read a Visium-style positions file → DataFrame indexed by barcode with x/y."""
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    # tissue_positions_list.csv is header-less; tissue_positions.csv has a header.
    with opener(path, "rt") as handle:
        first = handle.readline()
    has_header = "barcode" in first.lower() or "pxl" in first.lower()
    if has_header:
        df = pd.read_csv(path)
        bc = next((c for c in df.columns if "barcode" in c.lower()), df.columns[0])
        xc = next((c for c in df.columns if c.lower() in ("pxl_col_in_fullres", "x", "imagecol", "col")), None)
        yc = next((c for c in df.columns if c.lower() in ("pxl_row_in_fullres", "y", "imagerow", "row")), None)
        if xc is None or yc is None:
            num = df.select_dtypes("number").columns.tolist()
            xc, yc = num[-2], num[-1]
        out = pd.DataFrame({"x": df[xc].astype(float).values, "y": df[yc].astype(float).values},
                           index=df[bc].astype(str).values)
    else:
        df = pd.read_csv(path, header=None)
        # cols: barcode, in_tissue, array_row, array_col, pxl_row_in_fullres, pxl_col_in_fullres
        out = pd.DataFrame({"x": df.iloc[:, 5].astype(float).values,
                            "y": df.iloc[:, 4].astype(float).values},
                           index=df.iloc[:, 0].astype(str).values)
        if df.shape[1] > 1:
            out["in_tissue"] = df.iloc[:, 1].values
    return out


def _load_matrix(root: Path) -> Tuple[ad.AnnData, str]:
    """Load a peak/gene-activity matrix as AnnData (obs = barcodes, var = features)."""
    import scipy.io as sio
    from scipy.sparse import csr_matrix

    h5 = _find_first(root, ("filtered_peak_bc_matrix.h5", "peak_matrix.h5",
                            "gene_activity.h5", "matrix.h5", "raw_peak_bc_matrix.h5"))
    if h5 is not None:
        import h5py
        with h5py.File(h5, "r") as f:
            grp = f["matrix"] if "matrix" in f else f[list(f.keys())[0]]
            data = grp["data"][:]
            indices = grp["indices"][:]
            indptr = grp["indptr"][:]
            shape = tuple(grp["shape"][:])
            from scipy.sparse import csc_matrix
            X = csc_matrix((data, indices, indptr), shape=shape).T  # cells x features
            feats = grp["features"]["name"][:] if "features" in grp else grp["peaks"][:]
            features = [x.decode() if isinstance(x, bytes) else str(x) for x in feats]
            barcodes = [b.decode() if isinstance(b, bytes) else str(b) for b in grp["barcodes"][:]]
        adata = ad.AnnData(X=csr_matrix(X))
        adata.obs_names = barcodes
        adata.var_names = features
        return adata, str(h5)

    mtx = _find_first(root, ("matrix.mtx", "matrix.mtx.gz"))
    if mtx is not None:
        X = csr_matrix(sio.mmread(mtx)).T.tocsr()  # cells x features
        feat_path = _find_first(root, ("peaks.bed", "features.tsv", "features.tsv.gz",
                                       "peaks.tsv", "peaks.tsv.gz"))
        bc_path = _find_first(root, ("barcodes.tsv", "barcodes.tsv.gz"))
        if feat_path is None or bc_path is None:
            raise FileNotFoundError("MTX matrix found but features/barcodes missing")
        fopen = gzip.open if feat_path.name.endswith(".gz") else open
        bopen = gzip.open if bc_path.name.endswith(".gz") else open
        with fopen(feat_path, "rt") as fh:
            features = [line.split("\t")[0].strip().replace("\t", "_") for line in fh]
        with bopen(bc_path, "rt") as fh:
            barcodes = [line.strip() for line in fh]
        adata = ad.AnnData(X=X)
        adata.obs_names = barcodes[: X.shape[0]]
        adata.var_names = features[: X.shape[1]]
        return adata, str(mtx)

    raise FileNotFoundError("No peak/gene-activity matrix (.h5 or .mtx) found")


def read_spatial_atac_bundle(root: Path) -> ad.AnnData:
    """Load a spatial-ATAC matrix + positions into AnnData with ``obsm['spatial']``."""
    adata, matrix_src = _load_matrix(root)
    pos_path = _find_first(root, _POSITION_NAMES)
    if pos_path is None:
        raise FileNotFoundError(f"No tissue_positions file under {root}")
    pos = _read_positions(pos_path)

    adata.obs_names = adata.obs_names.astype(str)
    common = adata.obs_names.intersection(pos.index.astype(str))
    if common.empty:
        raise ValueError("No overlapping barcodes between matrix and positions")
    adata = adata[common].copy()
    pos = pos.loc[common]
    adata.obsm["spatial"] = pos[["x", "y"]].astype(float).values.astype(np.float32)
    adata.obs["x"] = adata.obsm["spatial"][:, 0]
    adata.obs["y"] = adata.obsm["spatial"][:, 1]
    if "in_tissue" in pos.columns:
        adata.obs["in_tissue"] = pos["in_tissue"].values
    adata.obs["total_counts"] = np.asarray(adata.X.sum(axis=1)).ravel()
    is_peak = bool(adata.var_names.str.contains(":|-").mean() > 0.5)
    adata.uns["spatial_atac"] = {
        "matrix_path": matrix_src,
        "positions_path": str(pos_path),
        "feature_type": "peaks" if is_peak else "gene_activity",
        "modality": "chromatin_accessibility",
    }
    return adata


def load_spatial_atac(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load spatial-ATAC bundle (dir/ZIP) or exported h5ad; return AnnData + meta."""
    path = Path(path)
    if path.suffix.lower() == ".h5ad":
        adata, meta = ingest_h5ad(path)
        meta["platform"] = "spatial_atac"
        meta["partial_support"] = True
        return adata, meta

    bundle_root, tmp = _resolve_bundle(path)
    try:
        h5ad_candidates = list(bundle_root.rglob("*.h5ad"))
        try:
            adata = read_spatial_atac_bundle(bundle_root)
        except FileNotFoundError:
            if h5ad_candidates:
                adata, meta = ingest_h5ad(h5ad_candidates[0])
                meta["platform"] = "spatial_atac"
                meta["note"] = "Loaded via exported h5ad fallback"
                return adata, meta
            raise
        detection = detect_platform(bundle_root)
        detection["platform"] = "spatial_atac"
        detection["technology_key"] = "spatial_atac"
        detection["modality"] = "atac"
        detection["missing"] = [m for m in detection.get("missing", []) if "stub" not in m.lower()]
        adata = normalize_to_contract(adata, platform="spatial_atac", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "spatial_atac",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
            "spatial_atac": adata.uns.get("spatial_atac", {}),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
