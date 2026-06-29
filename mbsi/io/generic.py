"""
Generic loaders for common file formats.

Handles:
  - .h5ad          — standard AnnData
  - .csv matrix    — count matrix (cells × genes)
  - .tsv matrix    — tab-separated variant
  - .mtx + features/barcodes — MEX format
  - coordinate CSV — paired x,y coordinates
  - ZIP of any of the above

All outputs pass through to_mbsi_contract for normalisation and stamping.
"""

from __future__ import annotations

import gzip
import io
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
# h5ad
# ---------------------------------------------------------------------------

def load_h5ad(source: Union[str, Path, io.IOBase]) -> ad.AnnData:
    """Load an h5ad file. Accepts a path or a file-like object."""
    if isinstance(source, (str, Path)):
        adata = ad.read_h5ad(source)
    else:
        with tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False) as tmp:
            tmp.write(source.read())
            tmp_path = tmp.name
        adata = ad.read_h5ad(tmp_path)

    has_spatial = "spatial" in adata.obsm
    return to_mbsi_contract(
        adata,
        platform="h5ad",
        display_name="AnnData (h5ad)",
        coordinate_type="cell" if has_spatial else "unknown",
        resolution="unknown",
        source_files=[getattr(source, "name", str(source))],
    )


# ---------------------------------------------------------------------------
# CSV / TSV matrix
# ---------------------------------------------------------------------------

def load_csv_matrix(
    counts_source: Union[str, Path, io.IOBase],
    coords_source: Optional[Union[str, Path, io.IOBase]] = None,
    separator: str = ",",
) -> ad.AnnData:
    """
    Load a count matrix CSV and an optional coordinates CSV.

    Parameters
    ----------
    counts_source : path or file-like
        Count matrix with genes as columns and cells/spots as rows.
        First column is used as row index if it contains non-numeric data.
    coords_source : path or file-like, optional
        CSV with at minimum 'x' and 'y' columns (case-insensitive).
    separator : str
        Field separator (',' or '\\t').

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    counts = pd.read_csv(counts_source, sep=separator, index_col=0)

    # Auto-detect if transposition is needed: genes should be columns (>obs)
    if counts.shape[0] > counts.shape[1] * 10:
        pass  # likely cells × genes already
    elif counts.shape[1] > counts.shape[0] * 10:
        counts = counts.T  # was genes × cells

    gene_cols = counts.select_dtypes(include=[np.number]).columns
    counts = counts[gene_cols]

    X = sp.csr_matrix(counts.values.astype(np.float32))
    adata = ad.AnnData(X=X)
    adata.var_names = list(counts.columns)
    adata.obs_names = counts.index.astype(str).tolist()

    if coords_source is not None:
        coords_df = pd.read_csv(coords_source)
        x_col = _find_col(coords_df.columns, ("x", "x_coord", "pxl_col", "col"))
        y_col = _find_col(coords_df.columns, ("y", "y_coord", "pxl_row", "row"))
        if x_col and y_col and len(coords_df) == adata.n_obs:
            adata.obsm["spatial"] = coords_df[[x_col, y_col]].values.astype(np.float64)
        elif x_col and y_col:
            # Try to align by index
            try:
                aligned = coords_df.set_index(coords_df.columns[0]).reindex(adata.obs_names)
                adata.obsm["spatial"] = aligned[[x_col, y_col]].values.astype(np.float64)
            except Exception:
                pass

    return to_mbsi_contract(
        adata,
        platform="csv",
        display_name="Generic CSV",
        coordinate_type="cell",
        resolution="unknown",
    )


# ---------------------------------------------------------------------------
# MEX (Matrix Exchange) format
# ---------------------------------------------------------------------------

def load_mex_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load MEX format: matrix.mtx[.gz], features.tsv[.gz], barcodes.tsv[.gz].

    Parameters
    ----------
    path : str or Path
        Directory containing matrix.mtx, features.tsv, barcodes.tsv.
    """
    import scipy.io

    path = Path(path)

    def _gz(name):
        gz = path / (name + ".gz")
        return gz if gz.exists() else path / name

    def _lines(p):
        if str(p).endswith(".gz"):
            with gzip.open(p, "rt") as fh:
                return [l.strip() for l in fh]
        return Path(p).read_text().splitlines()

    mtx_path = _gz("matrix.mtx")
    feat_path = _gz("features.tsv")
    bc_path = _gz("barcodes.tsv")

    X = sp.csr_matrix(scipy.io.mmread(str(mtx_path)).T, dtype=np.float32)
    rows = [l.split("\t") for l in _lines(feat_path) if l]
    gene_names = [r[1] if len(r) > 1 else r[0] for r in rows]
    barcodes = [l for l in _lines(bc_path) if l]

    adata = ad.AnnData(X=X)
    adata.var_names = gene_names
    adata.obs_names = barcodes

    return to_mbsi_contract(
        adata,
        platform="mex",
        display_name="MEX (matrix.mtx + features.tsv)",
        coordinate_type="cell",
        resolution="unknown",
    )


# ---------------------------------------------------------------------------
# ZIP dispatcher
# ---------------------------------------------------------------------------

def load_zip(zip_file) -> ad.AnnData:
    """
    Extract a ZIP and auto-detect / load the contents.

    Tries platform-specific loaders first (Visium → Xenium → MERFISH → CosMx),
    then falls back to generic h5ad / CSV.
    """
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        tmp_path = Path(tmp)
        file_names = [str(f.relative_to(tmp_path)) for f in tmp_path.rglob("*") if f.is_file()]

        from mbsi.io.detect import detect_platform
        result = detect_platform(file_names)

        if result.platform == "visium":
            from mbsi.io.visium import load_visium_dir, _find_space_ranger_root
            return load_visium_dir(_find_space_ranger_root(tmp_path))

        if result.platform == "xenium":
            from mbsi.io.xenium import load_xenium_dir, _find_xenium_root
            return load_xenium_dir(_find_xenium_root(tmp_path))

        if result.platform == "merfish":
            from mbsi.io.merfish import load_merfish_dir, _find_merfish_root
            return load_merfish_dir(_find_merfish_root(tmp_path))

        if result.platform == "cosmx":
            from mbsi.io.cosmx import load_cosmx_dir, _find_cosmx_root
            return load_cosmx_dir(_find_cosmx_root(tmp_path))

        if result.platform == "codex":
            from mbsi.io.codex import load_codex_dir, _find_codex_root
            return load_codex_dir(_find_codex_root(tmp_path))

        # Fallback: h5ad
        h5ads = list(tmp_path.rglob("*.h5ad"))
        if h5ads:
            return load_h5ad(h5ads[0])

        # Fallback: CSV
        csvs = list(tmp_path.rglob("*.csv"))
        if csvs:
            return load_csv_matrix(csvs[0])

        raise ValueError(
            f"Could not load ZIP contents. Detected platform: {result.platform}. "
            f"Files found: {file_names[:10]}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_col(columns, candidates):
    for c in candidates:
        for col in columns:
            if col.lower() == c.lower():
                return col
    return None
