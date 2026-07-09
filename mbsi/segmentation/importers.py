"""Import cell boundaries and segmentation masks from external formats."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from skimage.draw import polygon


def load_segmentation_mask(path: Union[str, Path]) -> np.ndarray:
    """Load a label or binary mask from .npy, TIFF, PNG, or JPEG."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".npy":
        arr = np.load(path)
    else:
        try:
            from skimage.io import imread
        except ImportError as exc:
            raise ValueError(f"Cannot import mask from {path}: skimage required") from exc
        arr = imread(path)
        if arr.ndim >= 3:
            arr = arr[..., 0]

    arr = np.asarray(arr)
    if arr.max() <= 1 and arr.dtype != np.int32:
        return (arr > 0).astype(np.int32)
    return arr.astype(np.int32)


def load_boundary_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Load boundary vertices from CSV (cell_id, x/y or vertex_x/vertex_y)."""
    path = Path(path)
    if path.suffix == ".gz" or path.name.endswith(".csv.gz"):
        with gzip.open(path, "rt") as handle:
            df = pd.read_csv(handle)
    else:
        df = pd.read_csv(path)

    rename = {}
    for col in df.columns:
        lower = col.lower()
        if lower in ("x", "vertex_x", "x_coord"):
            rename[col] = "vertex_x"
        elif lower in ("y", "vertex_y", "y_coord"):
            rename[col] = "vertex_y"
        elif lower in ("cell_id", "cell", "id", "label_id"):
            if lower != "cell_id":
                rename[col] = "cell_id"
    if rename:
        df = df.rename(columns=rename)

    required = {"cell_id", "vertex_x", "vertex_y"}
    missing = required - set(df.columns)
    if missing:
        alt_x = next((c for c in df.columns if c.lower() in ("x", "x_centroid")), None)
        alt_y = next((c for c in df.columns if c.lower() in ("y", "y_centroid")), None)
        id_col = next((c for c in df.columns if "cell" in c.lower() or c.lower() == "id"), None)
        if alt_x and alt_y and id_col:
            df = df.rename(columns={id_col: "cell_id", alt_x: "vertex_x", alt_y: "vertex_y"})
        else:
            raise ValueError(f"Boundary CSV missing columns: {sorted(missing)}")
    return df


def load_boundary_geojson(path: Union[str, Path]) -> pd.DataFrame:
    """Load boundary polygons from GeoJSON into a vertex dataframe."""
    path = Path(path)
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    rows = []
    features = data.get("features", [])
    for feat in features:
        props = feat.get("properties", {}) or {}
        cell_id = props.get("cell_id") or props.get("id") or props.get("label")
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", [])
        if geom.get("type") == "Polygon" and coords:
            ring = coords[0]
        elif geom.get("type") == "MultiPolygon" and coords:
            ring = coords[0][0]
        else:
            continue
        if cell_id is None:
            cell_id = len(rows)
        for x, y in ring:
            rows.append({"cell_id": str(cell_id), "vertex_x": float(x), "vertex_y": float(y)})

    if not rows:
        raise ValueError(f"No polygon features found in GeoJSON: {path}")
    return pd.DataFrame(rows)


def _load_boundaries_table(path: Path) -> pd.DataFrame:
    suffixes = "".join(path.suffixes).lower()
    if path.suffix.lower() == ".geojson":
        return load_boundary_geojson(path)
    if path.suffix.lower() in (".csv", ".gz") or suffixes.endswith(".csv.gz"):
        return load_boundary_csv(path)
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported boundary format: {path}")


def _normalize_boundaries_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rename = {}
    for col in out.columns:
        lower = col.lower()
        if lower in ("vertex_x", "x", "x_centroid"):
            rename[col] = "vertex_x"
        elif lower in ("vertex_y", "y", "y_centroid"):
            rename[col] = "vertex_y"
        elif lower in ("cell_id", "cell", "id"):
            if lower != "cell_id":
                rename[col] = "cell_id"
        elif lower == "label_id":
            rename[col] = "label_id"
    if rename:
        out = out.rename(columns=rename)
    if "cell_id" not in out.columns:
        out["cell_id"] = out.index.astype(str)
    out["cell_id"] = out["cell_id"].astype(str)
    return out


def rasterize_boundaries(
    boundaries_df: pd.DataFrame,
    shape: Optional[Tuple[int, int]] = None,
    pixel_size_microns: float = 1.0,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """Rasterize boundary vertices into an integer label mask."""
    df = _normalize_boundaries_df(boundaries_df)
    scale = 1.0 / max(pixel_size_microns, 1e-9)

    if shape is None:
        max_x = float(df["vertex_x"].max()) * scale
        max_y = float(df["vertex_y"].max()) * scale
        shape = (int(np.ceil(max_y)) + 2, int(np.ceil(max_x)) + 2)

    label_mask = np.zeros(shape, dtype=np.int32)
    centroids = []

    label_map = {}
    next_label = 1
    for cell_id, group in df.groupby("cell_id", sort=False):
        if "label_id" in group.columns:
            label = int(group["label_id"].iloc[0])
        else:
            label = label_map.get(cell_id)
            if label is None:
                label = next_label
                label_map[cell_id] = label
                next_label += 1

        xs = (group["vertex_x"].astype(float).values * scale).astype(np.int32)
        ys = (group["vertex_y"].astype(float).values * scale).astype(np.int32)
        if len(xs) < 3:
            continue
        rr, cc = polygon(ys, xs, shape=shape)
        label_mask[rr, cc] = label
        if len(xs):
            centroids.append(
                {
                    "cell_id": cell_id,
                    "label": label,
                    "x": float(np.mean(xs)),
                    "y": float(np.mean(ys)),
                }
            )

    centroid_df = pd.DataFrame(centroids)
    return label_mask, centroid_df


def load_xenium_boundaries(
    path: Union[str, Path],
    shape: Optional[Tuple[int, int]] = None,
    pixel_size_microns: float = 0.2125,
) -> Dict[str, Any]:
    """Load Xenium cell_boundaries.parquet (or CSV) and rasterize to a label mask."""
    path = Path(path)
    df = _normalize_boundaries_df(_load_boundaries_table(path))
    label_mask, centroids = rasterize_boundaries(
        df,
        shape=shape,
        pixel_size_microns=pixel_size_microns,
    )
    return {
        "label_mask": label_mask,
        "boundaries_df": df,
        "centroids": centroids,
        "n_cells": int(label_mask.max()),
        "source": str(path),
        "format": "xenium_boundaries",
    }
