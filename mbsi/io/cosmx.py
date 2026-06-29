"""
NanoString CosMx loader.

Supports:
  - *_exprMat_file.csv       — expression matrix (long or wide format)
  - *_metadata_file.csv      — cell metadata with centroid coordinates
  - *_fov_positions_file.csv — field-of-view positions (for µm conversion)
  - CellComposite/           — composite fluorescence images (optional)
  - *_tx_file.csv            — transcript molecule table (optional)
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

def load_cosmx_dir(path: Union[str, Path]) -> ad.AnnData:
    """
    Load a CosMx output directory.

    Parameters
    ----------
    path : str or Path
        Directory containing CosMx output files.

    Returns
    -------
    adata : AnnData  (MBSI contract)
    """
    path = Path(path)
    source_files: list = []

    expr_path = _find_file(path, "exprMat_file", source_files)
    meta_path = _find_file(path, "metadata_file", source_files)
    fov_path = _find_file(path, "fov_positions_file", source_files, required=False)

    if expr_path is None:
        raise FileNotFoundError(f"No *_exprMat_file.csv found in {path}")
    if meta_path is None:
        raise FileNotFoundError(f"No *_metadata_file.csv found in {path}")

    # --- Expression ---
    expr = pd.read_csv(expr_path)
    expr, cell_ids = _parse_expression(expr)

    # --- Metadata ---
    meta = pd.read_csv(meta_path)
    meta = _normalise_meta(meta, cell_ids)

    # --- FOV positions for global µm coordinates ---
    fov_offsets: Optional[pd.DataFrame] = None
    if fov_path is not None:
        fov_offsets = pd.read_csv(fov_path)

    # --- Build AnnData ---
    gene_cols = [c for c in expr.columns if not c.lower().startswith(("cell", "fov", "slide"))]
    X = sp.csr_matrix(expr[gene_cols].values.astype(np.float32))
    adata = ad.AnnData(X=X)
    adata.var_names = gene_cols
    adata.obs_names = cell_ids

    # Coordinates
    coords = _extract_coords(meta, fov_offsets)
    if coords is not None:
        adata.obsm["spatial"] = coords

    # Attach metadata
    for col in meta.columns[:30]:
        try:
            adata.obs[col] = meta[col].values[:adata.n_obs]
        except Exception:
            pass

    return to_mbsi_contract(
        adata,
        platform="cosmx",
        display_name="NanoString CosMx",
        coordinate_type="cell",
        resolution="single-cell",
        source_files=source_files,
    )


def load_cosmx_zip(zip_file) -> ad.AnnData:
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmp)
        root = _find_cosmx_root(Path(tmp))
        return load_cosmx_dir(root)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _find_file(path: Path, keyword: str, source_files: list, required: bool = True):
    matches = list(path.glob(f"*{keyword}*")) + list(path.rglob(f"*{keyword}*"))
    csv_matches = [m for m in matches if m.suffix in (".csv", ".gz") and m.is_file()]
    if csv_matches:
        source_files.append(csv_matches[0].name)
        return csv_matches[0]
    if required:
        return None
    return None


def _parse_expression(df: pd.DataFrame):
    """Handle both wide (cells × genes) and long formats."""
    id_candidates = ["cell_ID", "cell_id", "CellId", "Cell_ID"]
    id_col = next((c for c in id_candidates if c in df.columns), None)

    if id_col:
        cell_ids = df[id_col].astype(str).tolist()
        df = df.drop(columns=[id_col])
    else:
        cell_ids = [str(i) for i in range(len(df))]

    # Drop non-numeric or metadata columns
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df = df[num_cols]
    return df, cell_ids


def _normalise_meta(meta: pd.DataFrame, cell_ids: list) -> pd.DataFrame:
    id_candidates = ["cell_ID", "cell_id", "CellId"]
    id_col = next((c for c in id_candidates if c in meta.columns), None)
    if id_col:
        meta = meta.set_index(id_col)
        meta = meta.reindex(cell_ids)
    else:
        meta = meta.iloc[:len(cell_ids)].copy()
        meta.index = cell_ids
    return meta


def _extract_coords(
    meta: pd.DataFrame, fov_offsets: Optional[pd.DataFrame]
) -> Optional[np.ndarray]:
    x_col = next((c for c in meta.columns if c.lower() in ("x_centroid", "centerx", "x")), None)
    y_col = next((c for c in meta.columns if c.lower() in ("y_centroid", "centery", "y")), None)
    if x_col is None or y_col is None:
        return None

    x = meta[x_col].values.astype(float)
    y = meta[y_col].values.astype(float)

    # Add FOV global offset if available
    if fov_offsets is not None:
        fov_col = next((c for c in meta.columns if "fov" in c.lower()), None)
        if fov_col is not None:
            fx_col = next((c for c in fov_offsets.columns if "x" in c.lower()), None)
            fy_col = next((c for c in fov_offsets.columns if "y" in c.lower()), None)
            fid_col = next((c for c in fov_offsets.columns if "fov" in c.lower()), None)
            if fx_col and fy_col and fid_col:
                fov_map = fov_offsets.set_index(fid_col)[[fx_col, fy_col]]
                fovs = meta[fov_col].values
                for i, fov in enumerate(fovs):
                    if fov in fov_map.index:
                        x[i] += fov_map.loc[fov, fx_col]
                        y[i] += fov_map.loc[fov, fy_col]

    return np.column_stack([x, y])


def _find_cosmx_root(tmp: Path) -> Path:
    for candidate in [tmp] + list(tmp.rglob("*")):
        if candidate.is_dir():
            files = list(candidate.glob("*exprMat*"))
            if files:
                return candidate
    return tmp
