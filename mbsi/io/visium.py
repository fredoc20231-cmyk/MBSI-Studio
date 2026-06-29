"""
10x Visium / Visium HD loader.

Supports:
  - Space Ranger output directory (filtered or raw)
  - ZIP archive of a Space Ranger output directory
  - Legacy tissue_positions_list.csv (Visium v1)
  - New tissue_positions.csv (Visium HD / Space Ranger ≥2.0)
  - scalefactors_json.json for pixel→µm conversion
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional, Union

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import scipy.sparse as sp

from mbsi.io.converters import to_mbsi_contract


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_visium_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load a Space Ranger output directory into AnnData.

    Parameters
    ----------
    path : str or Path
        Root of Space Ranger output (contains filtered_feature_bc_matrix.h5
        or filtered_feature_bc_matrix/ and spatial/).

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    path = Path(path)
    source_files: list = []

    # --- Expression matrix ---
    adata = _load_expression(path, source_files)

    # --- Spatial coordinates ---
    coords, scale_um_per_px = _load_spatial(path, adata.n_obs, source_files)
    adata.obsm["spatial"] = coords

    if scale_um_per_px is not None:
        adata.uns.setdefault("spatial_scale", {})["um_per_px"] = scale_um_per_px

    # --- Histology image ---
    _load_images(path, adata)

    return to_mbsi_contract(
        adata,
        platform="visium",
        display_name="10x Visium",
        coordinate_type="spot",
        resolution="spot",
        source_files=source_files,
    )


def load_visium_zip(zip_file) -> ad.AnnData:
    """
    Load a ZIP archive of a Space Ranger output directory.

    Parameters
    ----------
    zip_file : file-like or Path
        ZIP file containing Space Ranger outputs.

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        root = _find_space_ranger_root(Path(tmp))
        return load_visium_dir(root)


# ---------------------------------------------------------------------------
# Expression matrix helpers
# ---------------------------------------------------------------------------

def _load_expression(path: Path, source_files: list) -> ad.AnnData:
    """Try HDF5 first, then MTX directory."""
    for prefix in ("filtered_feature_bc_matrix", "raw_feature_bc_matrix"):
        h5 = path / f"{prefix}.h5"
        if h5.exists():
            source_files.append(h5.name)
            return _read_h5_matrix(h5)
        mtx_dir = path / prefix
        if (mtx_dir / "matrix.mtx.gz").exists() or (mtx_dir / "matrix.mtx").exists():
            source_files.append(str(mtx_dir.name))
            return _read_mtx_dir(mtx_dir)

    raise FileNotFoundError(
        f"No expression matrix found in {path}. Expected "
        f"filtered_feature_bc_matrix.h5 or filtered_feature_bc_matrix/matrix.mtx[.gz]"
    )


def _read_h5_matrix(h5_path: Path) -> ad.AnnData:
    with h5py.File(h5_path, "r") as f:
        grp = f["matrix"]
        data = grp["data"][:]
        indices = grp["indices"][:]
        indptr = grp["indptr"][:]
        shape = tuple(grp["shape"][:])  # (n_genes, n_barcodes)

        def _decode(arr):
            return [v.decode() if isinstance(v, bytes) else v for v in arr]

        genes = _decode(grp["features"]["name"][:])
        gene_ids = _decode(grp["features"]["id"][:])
        barcodes = _decode(grp["barcodes"][:])

    # HDF5 shape is (genes × barcodes); transpose to (barcodes × genes)
    X = sp.csr_matrix((data, indices, indptr), shape=shape).T.astype(np.float32)
    adata = ad.AnnData(X=X)
    adata.var_names = genes
    adata.var["gene_ids"] = gene_ids
    adata.obs_names = barcodes
    return adata


def _read_mtx_dir(mtx_dir: Path) -> ad.AnnData:
    import scipy.io

    mtx = mtx_dir / "matrix.mtx.gz" if (mtx_dir / "matrix.mtx.gz").exists() else mtx_dir / "matrix.mtx"
    feat = mtx_dir / "features.tsv.gz" if (mtx_dir / "features.tsv.gz").exists() else mtx_dir / "features.tsv"
    bc = mtx_dir / "barcodes.tsv.gz" if (mtx_dir / "barcodes.tsv.gz").exists() else mtx_dir / "barcodes.tsv"

    import gzip
    def _read_lines(p: Path):
        if p.suffix == ".gz":
            with gzip.open(p, "rt") as fh:
                return [l.strip() for l in fh]
        return p.read_text().splitlines()

    X = sp.csr_matrix(scipy.io.mmread(str(mtx)).T, dtype=np.float32)
    features = [l.split("\t") for l in _read_lines(feat)]
    gene_ids = [r[0] for r in features]
    gene_names = [r[1] if len(r) > 1 else r[0] for r in features]
    barcodes = _read_lines(bc)

    adata = ad.AnnData(X=X)
    adata.var_names = gene_names
    adata.var["gene_ids"] = gene_ids
    adata.obs_names = barcodes
    return adata


# ---------------------------------------------------------------------------
# Spatial coordinate helpers
# ---------------------------------------------------------------------------

def _load_spatial(
    path: Path, n_obs: int, source_files: list
) -> tuple[np.ndarray, Optional[float]]:
    spatial_dir = path / "spatial"
    if not spatial_dir.exists():
        raise FileNotFoundError(f"No spatial/ directory in {path}")

    # Prefer HD format, then v2 CSV, then legacy list
    for name in ("tissue_positions.csv", "tissue_positions_list.csv"):
        pos_file = spatial_dir / name
        if pos_file.exists():
            source_files.append(pos_file.name)
            df = _read_positions(pos_file)
            break
    else:
        raise FileNotFoundError(f"No tissue_positions[_list].csv in {spatial_dir}")

    # scalefactors for µm conversion
    sf_file = spatial_dir / "scalefactors_json.json"
    scale_um_per_px: Optional[float] = None
    if sf_file.exists():
        source_files.append(sf_file.name)
        sf = json.loads(sf_file.read_text())
        # tissue_hires_scalef converts hires px to fullres px; spot_diameter_fullres in px
        spot_diam_px = sf.get("spot_diameter_fullres", None)
        if spot_diam_px:
            # Visium spots are 55 µm diameter
            scale_um_per_px = 55.0 / spot_diam_px

    coords = df[["pxl_row_in_fullres", "pxl_col_in_fullres"]].values.astype(np.float64)
    if scale_um_per_px is not None:
        coords = coords * scale_um_per_px

    return coords, scale_um_per_px


def _read_positions(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, header=None)
    # v1 (tissue_positions_list): barcode,in_tissue,row,col,pxl_row,pxl_col
    # v2 (tissue_positions):      barcode,in_tissue,array_row,array_col,pxl_row,pxl_col
    if df.shape[1] == 6:
        df.columns = ["barcode", "in_tissue", "array_row", "array_col",
                      "pxl_row_in_fullres", "pxl_col_in_fullres"]
    else:
        # HD or custom — read with header
        df = pd.read_csv(csv_path)
        # normalise column names
        col_map = {}
        for col in df.columns:
            lc = col.lower()
            if "pxl_row" in lc or "pixel_row" in lc:
                col_map[col] = "pxl_row_in_fullres"
            elif "pxl_col" in lc or "pixel_col" in lc:
                col_map[col] = "pxl_col_in_fullres"
        df = df.rename(columns=col_map)

    if "in_tissue" in df.columns:
        df = df[df["in_tissue"] == 1].reset_index(drop=True)

    return df


def _load_images(path: Path, adata: ad.AnnData) -> None:
    spatial_dir = path / "spatial"
    if not spatial_dir.exists():
        return
    images: Dict[str, np.ndarray] = {}
    for fname in ("tissue_hires_image.png", "tissue_lowres_image.png"):
        img_path = spatial_dir / fname
        if img_path.exists():
            try:
                from PIL import Image
                images[fname.replace(".png", "")] = np.array(Image.open(img_path))
            except Exception:
                pass
    if images:
        adata.uns.setdefault("spatial", {}).setdefault("images", {}).update(images)


# ---------------------------------------------------------------------------
# Root detection inside ZIP
# ---------------------------------------------------------------------------

def _find_space_ranger_root(tmp: Path) -> Path:
    """Walk tmp to find the directory containing filtered_feature_bc_matrix.h5."""
    for candidate in [tmp] + list(tmp.rglob("*")):
        if candidate.is_dir():
            if (candidate / "filtered_feature_bc_matrix.h5").exists():
                return candidate
            if (candidate / "filtered_feature_bc_matrix").is_dir():
                return candidate
    return tmp  # fallback


# ---------------------------------------------------------------------------
# Public convenience
# ---------------------------------------------------------------------------

def list_visium_files(path: Union[str, Path]) -> Dict[str, bool]:
    """Return presence/absence of all standard Visium files."""
    path = Path(path)
    checks = {
        "filtered_feature_bc_matrix.h5": (path / "filtered_feature_bc_matrix.h5").exists(),
        "raw_feature_bc_matrix.h5": (path / "raw_feature_bc_matrix.h5").exists(),
        "filtered_feature_bc_matrix/": (path / "filtered_feature_bc_matrix").is_dir(),
        "spatial/tissue_positions.csv": (path / "spatial" / "tissue_positions.csv").exists(),
        "spatial/tissue_positions_list.csv": (path / "spatial" / "tissue_positions_list.csv").exists(),
        "spatial/tissue_hires_image.png": (path / "spatial" / "tissue_hires_image.png").exists(),
        "spatial/tissue_lowres_image.png": (path / "spatial" / "tissue_lowres_image.png").exists(),
        "spatial/scalefactors_json.json": (path / "spatial" / "scalefactors_json.json").exists(),
    }
    return checks
