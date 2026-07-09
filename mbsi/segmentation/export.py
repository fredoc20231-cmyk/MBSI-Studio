"""Attach segmentation outputs to AnnData and export masks/boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import anndata as ad
import numpy as np
import pandas as pd
from skimage import measure
from skimage.segmentation import find_boundaries


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


def _mask_to_boundary_vertices(label_mask: np.ndarray) -> pd.DataFrame:
    """Extract boundary vertices from a label mask for export."""
    label_mask = np.asarray(label_mask, dtype=np.int32)
    rows = []
    for prop in measure.regionprops(label_mask):
        label = int(prop.label)
        coords = measure.find_contours(label_mask == label, 0.5)
        if not coords:
            continue
        contour = coords[0]
        ys, xs = contour[:, 0], contour[:, 1]
        for x, y in zip(xs, ys):
            rows.append({"cell_id": f"cell_{label}", "label_id": label, "vertex_x": float(x), "vertex_y": float(y)})
    return pd.DataFrame(rows)


def export_label_mask(path: Union[str, Path], label_mask: np.ndarray) -> str:
    """Save label mask as .npy or TIFF based on extension."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in (".tif", ".tiff"):
        try:
            from skimage.io import imsave
        except ImportError as exc:
            raise ImportError("skimage required for TIFF export") from exc
        imsave(path, label_mask.astype(np.int32))
    else:
        if path.suffix.lower() != ".npy":
            path = path.with_suffix(".npy")
        np.save(path, label_mask)
    return str(path)


def export_boundaries(
    path: Union[str, Path],
    label_mask: Optional[np.ndarray] = None,
    boundaries_df: Optional[pd.DataFrame] = None,
) -> str:
    """Export cell boundaries as GeoJSON or parquet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if boundaries_df is None:
        if label_mask is None:
            raise ValueError("Provide label_mask or boundaries_df for boundary export")
        boundaries_df = _mask_to_boundary_vertices(label_mask)

    suffix = path.suffix.lower()
    if suffix == ".parquet":
        boundaries_df.to_parquet(path, index=False)
    elif suffix == ".geojson":
        features = []
        for cell_id, group in boundaries_df.groupby("cell_id", sort=False):
            coords = list(zip(group["vertex_x"].astype(float), group["vertex_y"].astype(float)))
            if coords and coords[0] != coords[-1]:
                coords.append(coords[0])
            features.append(
                {
                    "type": "Feature",
                    "properties": {"cell_id": str(cell_id)},
                    "geometry": {"type": "Polygon", "coordinates": [coords]},
                }
            )
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"type": "FeatureCollection", "features": features}, handle)
    else:
        path = path.with_suffix(".parquet")
        boundaries_df.to_parquet(path, index=False)
    return str(path)


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
    from mbsi.segmentation.importers import load_segmentation_mask

    return load_segmentation_mask(path)


def import_cell_boundaries(path: str | Path) -> Dict[str, Any]:
    """Import cell boundaries from GeoJSON, CSV, or parquet."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".geojson":
        from mbsi.segmentation.importers import load_boundary_geojson

        df = load_boundary_geojson(path)
        return {"format": "geojson", "dataframe": df, "n_features": df["cell_id"].nunique()}
    if suffix in (".csv", ".gz") or path.name.endswith(".csv.gz"):
        from mbsi.segmentation.importers import load_boundary_csv

        df = load_boundary_csv(path)
        return {"format": "csv", "dataframe": df, "n_rows": len(df)}
    if suffix == ".parquet":
        df = pd.read_parquet(path)
        return {"format": "parquet", "dataframe": df, "n_rows": len(df)}
    raise ValueError(f"Unsupported boundary format: {suffix}")
