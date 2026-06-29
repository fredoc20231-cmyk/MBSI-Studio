"""
CODEX / PhenoCycler / MIBI loader.

Supports:
  - cell_table.csv           — cell-level protein expression + coordinates
  - channel_names.txt        — marker/antibody panel names
  - *.ome.tif                — multichannel image (optional, memory-mapped)
  - cell_masks.tif           — segmentation mask (optional)

CODEX produces protein expression, not RNA. This loader stores it in
adata.X with protein markers as var_names, and marks the modality as
'protein' in uns['mbsi_platform'].
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


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_codex_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load a CODEX output directory.

    Parameters
    ----------
    path : str or Path
        Directory containing cell_table.csv (or equivalent).

    Returns
    -------
    adata : AnnData  (MBSI contract, modality='protein')
    """
    path = Path(path)
    source_files: list = []

    cell_table = _load_cell_table(path, source_files)
    channel_names = _load_channel_names(path, source_files)

    # Identify protein-expression columns vs. metadata columns
    meta_keywords = {"cell", "fov", "label", "id", "x", "y", "area", "eccentricity",
                     "major", "minor", "solidity", "region", "slide", "sample"}

    if channel_names:
        protein_cols = [c for c in cell_table.columns if c in channel_names]
    else:
        protein_cols = [
            c for c in cell_table.select_dtypes(include=[np.number]).columns
            if not any(kw in c.lower() for kw in meta_keywords)
        ]

    if not protein_cols:
        raise ValueError(
            "Could not identify protein-expression columns in cell_table. "
            "Provide channel_names.txt or ensure numeric columns represent markers."
        )

    X = sp.csr_matrix(cell_table[protein_cols].fillna(0).values.astype(np.float32))
    adata = ad.AnnData(X=X)
    adata.var_names = protein_cols
    adata.var["modality"] = "protein"

    # Spatial coordinates
    x_col = next((c for c in cell_table.columns if c.lower() in ("x", "centroid_x", "x_centroid")), None)
    y_col = next((c for c in cell_table.columns if c.lower() in ("y", "centroid_y", "y_centroid")), None)
    if x_col and y_col:
        coords = cell_table[[x_col, y_col]].values.astype(np.float64)
        adata.obsm["spatial"] = coords

    adata.obs_names = cell_table.index.astype(str).tolist()

    # Attach remaining metadata
    meta_cols = [c for c in cell_table.columns if c not in protein_cols]
    for col in meta_cols[:20]:
        try:
            adata.obs[col] = cell_table[col].values
        except Exception:
            pass

    return to_mbsi_contract(
        adata,
        platform="codex",
        display_name="CODEX / PhenoCycler",
        coordinate_type="cell",
        resolution="single-cell",
        source_files=source_files,
        extra={"modality": "protein", "n_markers": len(protein_cols)},
    )


def load_codex_zip(zip_file) -> ad.AnnData:
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        root = _find_codex_root(Path(tmp))
        return load_codex_dir(root)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_cell_table(path: Path, source_files: list) -> pd.DataFrame:
    candidates = ["cell_table.csv", "cell_table.csv.gz", "cell_data.csv",
                  "cells.csv", "CellData.csv", "expression_matrix.csv"]
    for name in candidates:
        p = path / name
        if p.exists():
            source_files.append(name)
            return pd.read_csv(p, index_col=0)
    # Glob fallback
    csvs = list(path.glob("*.csv")) + list(path.glob("*.csv.gz"))
    if csvs:
        source_files.append(csvs[0].name)
        return pd.read_csv(csvs[0], index_col=0)
    raise FileNotFoundError(f"No cell table CSV found in {path}")


def _load_channel_names(path: Path, source_files: list) -> Optional[list]:
    for name in ("channel_names.txt", "markers.txt", "panel.txt"):
        p = path / name
        if p.exists():
            source_files.append(name)
            return [l.strip() for l in p.read_text().splitlines() if l.strip()]
    return None


def _find_codex_root(tmp: Path) -> Path:
    for candidate in [tmp] + list(tmp.rglob("*")):
        if candidate.is_dir():
            if any(candidate.glob("cell_table*")) or any(candidate.glob("*.csv")):
                return candidate
    return tmp
