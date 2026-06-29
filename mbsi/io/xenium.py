"""
10x Xenium loader.

Supports:
  - cell_feature_matrix.h5  (primary expression source)
  - cells.csv.gz / cells.parquet  (cell centroids + metadata)
  - transcripts.csv.gz / transcripts.parquet  (molecule table, optional)
  - nucleus_boundaries.csv / cell_boundaries.csv  (optional)
  - morphology_focus.ome.tif / morphology.ome.tif  (optional)
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.converters import to_mbsi_contract


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_xenium_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load a Xenium output directory.

    Parameters
    ----------
    path : str or Path
        Root of Xenium output directory.

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    path = Path(path)
    source_files: list = []

    # --- Expression matrix ---
    adata = _load_xenium_expression(path, source_files)

    # --- Cell centroids ---
    cells_df = _load_cells(path, source_files)
    if cells_df is not None:
        _merge_cell_metadata(adata, cells_df)

    # --- Optional: transcripts (molecule table) ---
    tx = _load_transcripts(path)
    if tx is not None:
        adata.uns["transcripts"] = tx.head(100_000)  # cap for memory

    return to_mbsi_contract(
        adata,
        platform="xenium",
        display_name="10x Xenium",
        coordinate_type="cell",
        resolution="single-cell",
        source_files=source_files,
    )


def load_xenium_zip(zip_file) -> ad.AnnData:
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        root = _find_xenium_root(Path(tmp))
        return load_xenium_dir(root)


# ---------------------------------------------------------------------------
# Expression
# ---------------------------------------------------------------------------

def _load_xenium_expression(path: Path, source_files: list) -> ad.AnnData:
    h5 = path / "cell_feature_matrix.h5"
    if h5.exists():
        source_files.append(h5.name)
        import h5py, scipy.sparse as sp

        with h5py.File(h5, "r") as f:
            grp = f["matrix"]

            def _d(arr):
                return [v.decode() if isinstance(v, bytes) else v for v in arr]

            data = grp["data"][:]
            indices = grp["indices"][:]
            indptr = grp["indptr"][:]
            shape = tuple(grp["shape"][:])
            genes = _d(grp["features"]["name"][:])
            barcodes = _d(grp["barcodes"][:])

        X = sp.csr_matrix((data, indices, indptr), shape=shape).T.astype(np.float32)
        adata = ad.AnnData(X=X)
        adata.var_names = genes
        adata.obs_names = barcodes
        return adata

    # Fallback: MTX directory
    mtx_dir = path / "cell_feature_matrix"
    if mtx_dir.is_dir():
        source_files.append("cell_feature_matrix/")
        return _read_mtx_dir(mtx_dir)

    raise FileNotFoundError(
        f"No cell_feature_matrix.h5 or cell_feature_matrix/ found in {path}"
    )


def _read_mtx_dir(mtx_dir: Path) -> ad.AnnData:
    import gzip, scipy.io, scipy.sparse as sp

    def _gz(p: Path, alt: Path):
        return p if p.exists() else alt

    mtx = _gz(mtx_dir / "matrix.mtx.gz", mtx_dir / "matrix.mtx")
    feat = _gz(mtx_dir / "features.tsv.gz", mtx_dir / "features.tsv")
    bc = _gz(mtx_dir / "barcodes.tsv.gz", mtx_dir / "barcodes.tsv")

    def _lines(p: Path):
        if p.suffix == ".gz":
            with gzip.open(p, "rt") as fh:
                return [l.strip() for l in fh]
        return p.read_text().splitlines()

    X = sp.csr_matrix(scipy.io.mmread(str(mtx)).T, dtype=np.float32)
    rows = [l.split("\t") for l in _lines(feat)]
    genes = [r[1] if len(r) > 1 else r[0] for r in rows]
    barcodes = _lines(bc)

    adata = ad.AnnData(X=X)
    adata.var_names = genes
    adata.obs_names = barcodes
    return adata


# ---------------------------------------------------------------------------
# Cell metadata / centroids
# ---------------------------------------------------------------------------

def _load_cells(path: Path, source_files: list) -> Optional[pd.DataFrame]:
    for name in ("cells.parquet", "cells.csv.gz", "cells.csv"):
        p = path / name
        if p.exists():
            source_files.append(name)
            if name.endswith(".parquet"):
                return pd.read_parquet(p)
            return pd.read_csv(p)
    return None


def _merge_cell_metadata(adata: ad.AnnData, cells: pd.DataFrame) -> None:
    """Attach centroids and quality metrics from cells table."""
    # Align on cell_id / index
    id_col = next((c for c in cells.columns if "cell_id" in c.lower()), None)
    if id_col:
        cells = cells.set_index(id_col)

    # Spatial coordinates
    x_col = next((c for c in cells.columns if c.lower() in ("x_centroid", "x")), None)
    y_col = next((c for c in cells.columns if c.lower() in ("y_centroid", "y")), None)
    if x_col and y_col:
        # Align to adata.obs_names
        try:
            aligned = cells.reindex(adata.obs_names)
        except Exception:
            aligned = cells.iloc[:adata.n_obs]
        coords = aligned[[x_col, y_col]].values.astype(np.float64)
        adata.obsm["spatial"] = coords

    # Quality metrics
    quality_cols = [c for c in cells.columns if any(
        kw in c.lower() for kw in ("transcript", "quality", "nucleus", "area")
    )]
    for col in quality_cols:
        try:
            aligned = cells.reindex(adata.obs_names)[col]
            adata.obs[col] = aligned.values
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Transcripts (molecule table)
# ---------------------------------------------------------------------------

def _load_transcripts(path: Path) -> Optional[pd.DataFrame]:
    for name in ("transcripts.parquet", "transcripts.csv.gz", "transcripts.csv"):
        p = path / name
        if p.exists():
            try:
                if name.endswith(".parquet"):
                    return pd.read_parquet(p)
                return pd.read_csv(p, nrows=500_000)
            except Exception:
                return None
    return None


# ---------------------------------------------------------------------------
# Root detection
# ---------------------------------------------------------------------------

def _find_xenium_root(tmp: Path) -> Path:
    for candidate in [tmp] + list(tmp.rglob("*")):
        if candidate.is_dir() and (candidate / "cell_feature_matrix.h5").exists():
            return candidate
    return tmp
