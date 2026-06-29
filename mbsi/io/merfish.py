"""
MERFISH / MERSCOPE loader.

Supports Vizgen MERSCOPE output:
  - cell_by_gene.csv          — cell × gene expression matrix
  - cell_metadata.csv         — cell centroids and metadata
  - detected_transcripts.csv  — molecule table (optional, large)
  - cell_boundaries/          — parquet files per z-slice (optional)
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Union

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

from mbsi.io.converters import to_mbsi_contract


def load_merfish_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load a MERSCOPE output directory.

    Parameters
    ----------
    path : str or Path
        Root directory containing cell_by_gene.csv and cell_metadata.csv.

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    path = Path(path)
    source_files: list = []

    # --- Expression matrix ---
    cbg = _load_cell_by_gene(path, source_files)

    # --- Cell metadata / centroids ---
    meta = _load_cell_metadata(path, source_files)

    # --- Build AnnData ---
    X = sp.csr_matrix(cbg.values.astype(np.float32))
    adata = ad.AnnData(X=X)
    adata.var_names = list(cbg.columns)
    adata.obs_names = cbg.index.astype(str).tolist()

    # Spatial coordinates
    if meta is not None:
        aligned = meta.reindex(cbg.index)
        x_col = _find_col(meta.columns, ("center_x", "x", "x_centroid"))
        y_col = _find_col(meta.columns, ("center_y", "y", "y_centroid"))
        if x_col and y_col:
            coords = aligned[[x_col, y_col]].values.astype(np.float64)
            adata.obsm["spatial"] = coords

        # Copy other metadata columns
        meta_cols = [c for c in meta.columns if c not in (x_col, y_col)]
        for col in meta_cols[:20]:  # cap to avoid massive obs tables
            try:
                adata.obs[col] = aligned[col].values
            except Exception:
                pass

    # --- Optional: molecule table ---
    tx = _load_transcripts(path)
    if tx is not None:
        adata.uns["transcripts"] = tx

    return to_mbsi_contract(
        adata,
        platform="merfish",
        display_name="MERFISH / MERSCOPE",
        coordinate_type="cell",
        resolution="single-cell",
        source_files=source_files,
    )


def load_merfish_zip(zip_file) -> ad.AnnData:
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        root = _find_merfish_root(Path(tmp))
        return load_merfish_dir(root)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_cell_by_gene(path: Path, source_files: list) -> pd.DataFrame:
    for name in ("cell_by_gene.csv", "cell_by_gene.csv.gz"):
        p = path / name
        if p.exists():
            source_files.append(name)
            df = pd.read_csv(p, index_col=0)
            # Drop non-gene columns that Vizgen includes
            drop_cols = [c for c in df.columns if c.lower().startswith("blank")]
            df = df.drop(columns=drop_cols, errors="ignore")
            return df
    raise FileNotFoundError(f"No cell_by_gene.csv found in {path}")


def _load_cell_metadata(path: Path, source_files: list) -> Optional[pd.DataFrame]:
    for name in ("cell_metadata.csv", "cell_metadata.csv.gz"):
        p = path / name
        if p.exists():
            source_files.append(name)
            return pd.read_csv(p, index_col=0)
    return None


def _load_transcripts(path: Path) -> Optional[pd.DataFrame]:
    for name in ("detected_transcripts.csv", "detected_transcripts.csv.gz"):
        p = path / name
        if p.exists():
            try:
                return pd.read_csv(p, nrows=200_000)
            except Exception:
                return None
    return None


def _find_col(columns, candidates):
    for c in candidates:
        for col in columns:
            if col.lower() == c.lower():
                return col
    return None


def _find_merfish_root(tmp: Path) -> Path:
    for candidate in [tmp] + list(tmp.rglob("*")):
        if candidate.is_dir() and (candidate / "cell_by_gene.csv").exists():
            return candidate
    return tmp
