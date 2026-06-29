"""Attach segmentation outputs to AnnData and export masks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
import pandas as pd


def attach_segmentation_to_adata(
    adata: ad.AnnData,
    tissue_mask: Optional[np.ndarray] = None,
    nuclei_mask: Optional[np.ndarray] = None,
    cell_mask: Optional[np.ndarray] = None,
    cell_boundaries: Optional[np.ndarray] = None,
    compartment_labels: Optional[np.ndarray] = None,
    boundary_map: Optional[np.ndarray] = None,
    segmentation_qc: Optional[Dict[str, Any]] = None,
    methods: Optional[Dict[str, str]] = None,
) -> ad.AnnData:
    """Write segmentation outputs to obs/uns."""
    adata = adata.copy()
    meta: Dict[str, Any] = {"methods": methods or {}}

    if tissue_mask is not None and tissue_mask.ndim == 1 and len(tissue_mask) == adata.n_obs:
        adata.obs["tissue_region"] = tissue_mask.astype(int)
    elif tissue_mask is not None and tissue_mask.ndim >= 2:
        meta["tissue_mask_shape"] = list(tissue_mask.shape)

    if cell_mask is not None:
        if cell_mask.ndim == 1 and len(cell_mask) == adata.n_obs:
            adata.obs["segmentation_cell_id"] = cell_mask.astype(str)
        elif cell_mask.ndim >= 2:
            meta["cell_mask_shape"] = list(cell_mask.shape)

    if compartment_labels is not None and len(compartment_labels) == adata.n_obs:
        from mbsi.segmentation.compartments import COMPARTMENT_NAMES
        adata.obs["compartment"] = [
            COMPARTMENT_NAMES[int(c) % len(COMPARTMENT_NAMES)] if c >= 0 else "unknown"
            for c in compartment_labels
        ]

    if boundary_map is not None and boundary_map.ndim == 1 and len(boundary_map) == adata.n_obs:
        adata.obs["boundary_score"] = boundary_map.astype(np.float32)

    if cell_boundaries is not None:
        meta["cell_boundaries"] = "attached"

    adata.uns["mbsi_segmentation"] = meta
    if segmentation_qc is not None:
        adata.uns["mbsi_segmentation_qc"] = segmentation_qc
    return adata


def export_segmentation_masks(
    out_dir: Path,
    tissue_mask: Optional[np.ndarray] = None,
    nuclei_mask: Optional[np.ndarray] = None,
    cell_mask: Optional[np.ndarray] = None,
    boundary_map: Optional[np.ndarray] = None,
    prefix: str = "segmentation",
) -> Dict[str, str]:
    """Export masks as .npy files."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, str] = {}
    for name, arr in [
        ("tissue", tissue_mask),
        ("nuclei", nuclei_mask),
        ("cells", cell_mask),
        ("boundaries", boundary_map),
    ]:
        if arr is not None and getattr(arr, "ndim", 0) >= 2:
            p = out_dir / f"{prefix}_{name}.npy"
            np.save(p, arr)
            paths[name] = str(p)
    return paths


def import_segmentation_mask(path: str | Path) -> np.ndarray:
    """Import segmentation mask from .npy, .tif, or image file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".npy":
        return np.load(path)
    try:
        from skimage.io import imread
        arr = imread(path)
        if arr.ndim >= 3:
            arr = arr[..., 0]
        return (arr > 0).astype(np.uint8) if arr.max() <= 1 else arr.astype(np.int32)
    except Exception as exc:
        raise ValueError(f"Cannot import mask from {path}: {exc}") from exc


def import_cell_boundaries(path: str | Path) -> Dict[str, Any]:
    """Import cell boundaries from GeoJSON or CSV."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".geojson":
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {"format": "geojson", "data": data, "n_features": len(data.get("features", []))}
    if suffix == ".csv":
        df = pd.read_csv(path)
        coords_cols = [c for c in df.columns if c.lower() in ("x", "y", "cell_id", "boundary")]
        return {"format": "csv", "dataframe": df, "columns": coords_cols, "n_rows": len(df)}
    raise ValueError(f"Unsupported boundary format: {suffix}")
