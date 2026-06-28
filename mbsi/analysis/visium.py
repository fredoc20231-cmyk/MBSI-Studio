"""10x Space Ranger / Visium data loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.io import mmread
from scipy.sparse import csr_matrix


def load_tissue_positions(outs_dir: Union[str, Path]) -> pd.DataFrame:
    """Load tissue_positions.csv (headered or legacy headerless format)."""
    outs_dir = Path(outs_dir)
    spatial = outs_dir / "spatial"
    for name in ("tissue_positions.csv", "tissue_positions_list.csv"):
        path = spatial / name
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "barcode" not in df.columns and df.shape[1] >= 6:
            df = pd.read_csv(path, header=None, names=[
                "barcode", "in_tissue", "array_row", "array_col",
                "pxl_row_in_fullres", "pxl_col_in_fullres",
            ])
        return df
    raise FileNotFoundError(f"No tissue positions file in {spatial}")


def load_scalefactors(outs_dir: Union[str, Path]) -> Dict[str, float]:
    """Load scalefactors_json.json."""
    path = Path(outs_dir) / "spatial" / "scalefactors_json.json"
    if not path.exists():
        return {"tissue_hires_scalef": 1.0, "tissue_lowres_scalef": 0.1}
    return json.loads(path.read_text())


def load_spatial_image(outs_dir: Union[str, Path], res: str = "hires") -> np.ndarray:
    """Load tissue_hires_image.png or tissue_lowres_image.png."""
    from PIL import Image

    spatial = Path(outs_dir) / "spatial"
    fname = "tissue_hires_image.png" if res == "hires" else "tissue_lowres_image.png"
    path = spatial / fname
    if not path.exists():
        raise FileNotFoundError(path)
    return np.array(Image.open(path))


def _load_matrix(outs_dir: Path) -> tuple[csr_matrix, list, list]:
    h5_path = outs_dir / "filtered_feature_bc_matrix.h5"
    mtx_dir = outs_dir / "filtered_feature_bc_matrix"
    mtx_path = mtx_dir / "matrix.mtx"

    if h5_path.exists():
        with h5py.File(h5_path, "r") as f:
            mat = f["matrix"]
            data = mat["data"][:]
            indices = mat["indices"][:]
            indptr = mat["indptr"][:]
            shape = tuple(mat["shape"][:])
            X = csr_matrix((data, indices, indptr), shape=shape).T
            genes = [
                g.decode() if isinstance(g, bytes) else str(g)
                for g in mat["features"]["name"][:]
            ]
            barcodes = [
                b.decode() if isinstance(b, bytes) else str(b)
                for b in mat["barcodes"][:]
            ]
        return X, genes, barcodes

    if mtx_path.exists():
        X = csr_matrix(mmread(mtx_path).T)
        genes = pd.read_csv(mtx_dir / "features.tsv", sep="\t", header=None)[0].astype(str).tolist()
        barcodes = pd.read_csv(mtx_dir / "barcodes.tsv", sep="\t", header=None)[0].astype(str).tolist()
        return X, genes, barcodes

    raise FileNotFoundError(f"No count matrix in {outs_dir}")


def read_visium_spaceranger(outs_dir: str, image_res: str = "lowres") -> ad.AnnData:
    """
    Load a 10x Space Ranger outs directory.

    Returns AnnData with obsm['spatial'], obs in_tissue/array_row/array_col, uns spatial.
    """
    outs_dir = Path(outs_dir)
    X, genes, barcodes = _load_matrix(outs_dir)
    pos = load_tissue_positions(outs_dir)
    pos = pos.set_index("barcode")

    common = [b for b in barcodes if b in pos.index]
    if not common:
        pos.index = pos.index.astype(str)
        common = [b for b in barcodes if b in pos.index]

    idx = [barcodes.index(b) for b in common]
    X = X[idx, :]
    barcodes = common
    pos = pos.loc[barcodes]

    if "pxl_col_in_fullres" in pos.columns:
        coords = pos[["pxl_col_in_fullres", "pxl_row_in_fullres"]].values.astype(np.float32)
    else:
        coords = pos[["array_col", "array_row"]].values.astype(np.float32)

    adata = ad.AnnData(X=X)
    adata.var_names = genes
    adata.obs_names = barcodes
    adata.obsm["spatial"] = coords
    adata.obs["in_tissue"] = pos["in_tissue"].astype(bool).values if "in_tissue" in pos.columns else True
    adata.obs["array_row"] = pos["array_row"].astype(int).values if "array_row" in pos.columns else 0
    adata.obs["array_col"] = pos["array_col"].astype(int).values if "array_col" in pos.columns else 0

    library_id = "sample"
    scalefactors = load_scalefactors(outs_dir)
    images: Dict[str, Any] = {}
    for res_key, fname in [("hires", "tissue_hires_image.png"), ("lowres", "tissue_lowres_image.png")]:
        img_path = outs_dir / "spatial" / fname
        if img_path.exists():
            try:
                images[res_key] = load_spatial_image(outs_dir, res="hires" if res_key == "hires" else "lowres")
            except Exception:
                pass

    adata.uns["spatial"] = {library_id: {"images": images, "scalefactors": scalefactors}}
    adata.uns["spatial"]["library_id"] = library_id
    return adata
