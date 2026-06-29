"""Generic h5ad and CSV matrix + coordinates loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Union

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import detect_platform
from mbsi.io.validators import compute_readiness


def load_h5ad(path: Union[str, Path]) -> ad.AnnData:
    return ad.read_h5ad(path)


def load_csv_matrix_coords(
    matrix: pd.DataFrame,
    coordinates: pd.DataFrame,
) -> ad.AnnData:
    """Build AnnData from count matrix and coordinate table."""
    coords = coordinates.copy()
    if "x" not in coords.columns or "y" not in coords.columns:
        raise ValueError("Coordinates must include 'x' and 'y' columns")

    mat = matrix.copy()
    if mat.index.intersection(coords.index).size >= max(3, min(len(mat), len(coords)) // 2):
        shared = mat.index.intersection(coords.index)
        mat = mat.loc[shared]
        coords = coords.loc[shared]
    else:
        n = min(len(mat), len(coords))
        mat = mat.iloc[:n]
        coords = coords.iloc[:n]

    spatial = coords[["x", "y"]].astype(float).values
    adata = ad.AnnData(
        X=mat.values,
        obs=pd.DataFrame(index=mat.index.astype(str)),
        var=pd.DataFrame(index=mat.columns.astype(str)),
    )
    adata.obsm["spatial"] = spatial.astype(np.float32)
    adata.obs["x"] = spatial[:, 0]
    adata.obs["y"] = spatial[:, 1]
    return adata


def ingest_h5ad(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    path = Path(path)
    detection = detect_platform(path)
    adata = load_h5ad(path)
    platform = detection.get("platform", "generic_h5ad")
    adata = normalize_to_contract(adata, platform=platform, detection=detection)
    score, readiness = compute_readiness(adata, detection)
    return adata, {
        "platform": platform,
        "detection": detection,
        "readiness_score": score,
        "readiness": readiness,
        "source": str(path),
    }


def ingest_csv_matrix_coords(
    matrix: pd.DataFrame,
    coordinates: pd.DataFrame,
) -> Tuple[ad.AnnData, Dict[str, Any]]:
    detection = detect_platform({"matrix.csv": "matrix", "coordinates.csv": "coords"})
    detection["platform"] = "csv_matrix"
    adata = load_csv_matrix_coords(matrix, coordinates)
    adata = normalize_to_contract(adata, platform="csv_matrix", detection=detection)
    score, readiness = compute_readiness(adata, detection)
    return adata, {
        "platform": "csv_matrix",
        "detection": detection,
        "readiness_score": score,
        "readiness": readiness,
    }
