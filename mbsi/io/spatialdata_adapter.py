"""Optional SpatialData adapter — AnnData minimum always supported."""

from __future__ import annotations

import warnings
from typing import Any, Optional

import anndata as ad


def _spatialdata_available() -> bool:
    try:
        import spatialdata  # noqa: F401

        return True
    except ImportError:
        return False


def to_spatialdata(adata: ad.AnnData) -> Optional[Any]:
    """Wrap AnnData as SpatialData when spatialdata is installed; else warn and return None."""
    if not _spatialdata_available():
        warnings.warn(
            "spatialdata not installed — using AnnData contract only (Milestone 1 OK).",
            stacklevel=2,
        )
        return None

    try:
        from spatialdata.models import TableModel, PointsModel
        import numpy as np

        coords = adata.obsm.get("spatial")
        if coords is None:
            warnings.warn("AnnData missing obsm['spatial'] — cannot build SpatialData.", stacklevel=2)
            return None

        from spatialdata import SpatialData

        table = TableModel.parse(adata, region_key="cell_id", region=None)
        points = PointsModel.parse(
            np.column_stack([coords[:, 0], coords[:, 1], np.zeros(len(coords))]),
            transformations={},
        )
        return SpatialData(table=table, points={"centroids": points})
    except Exception as exc:
        warnings.warn(f"SpatialData conversion failed: {exc}", stacklevel=2)
        return None


def from_spatialdata(sd: Any) -> ad.AnnData:
    """Import primary table from SpatialData; raises when spatialdata unavailable."""
    if not _spatialdata_available():
        raise ImportError(
            "spatialdata not installed — use AnnData loaders for Milestone 1 (Visium/Xenium)."
        )
    if hasattr(sd, "tables") and sd.tables:
        key = next(iter(sd.tables.keys()))
        return sd.tables[key].to_anndata()
    raise ValueError("SpatialData object has no tables to convert.")
