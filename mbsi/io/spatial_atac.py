"""Spatial ATAC loader — stub with detection hints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Union

import anndata as ad

from mbsi.io.generic import ingest_h5ad
from mbsi.io.detect import detect_platform


def load_spatial_atac(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load spatial ATAC when exported as h5ad; full peak/fragment parse is stub."""
    path = Path(path)
    detection = detect_platform(path if path.is_dir() else [path.name])
    h5ad_candidates = list(path.rglob("*.h5ad")) if path.is_dir() else ([path] if path.suffix.lower() == ".h5ad" else [])
    if h5ad_candidates:
        adata, meta = ingest_h5ad(h5ad_candidates[0])
        meta["platform"] = "spatial_atac"
        meta["partial_support"] = True
        meta["note"] = "Loaded via h5ad fallback; fragment/BAM parse not implemented"
        return adata, meta
    raise NotImplementedError(
        "Spatial ATAC full loader is stub — provide peak matrix h5ad or use generic_h5ad. "
        f"Detection: {detection.get('platform')}"
    )
