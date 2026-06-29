"""Optional SpatialData adapter — AnnData minimum always supported."""

from __future__ import annotations

from typing import Any, Optional

import anndata as ad


def to_spatialdata(adata: ad.AnnData) -> Any:
    """Phase 2+: wrap AnnData as SpatialData. Not required for MBSI pipelines."""
    raise NotImplementedError("SpatialData adapter is optional — use AnnData contract for Phase 1")


def from_spatialdata(sd: Any) -> ad.AnnData:
    raise NotImplementedError("SpatialData import is Phase 2+")
