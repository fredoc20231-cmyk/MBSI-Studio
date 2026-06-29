"""10x Xenium loader — Phase 2 stub with basic h5ad fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple, Union

import anndata as ad

from mbsi.io.generic import ingest_h5ad


def load_xenium(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Phase 2: full Xenium bundle. Phase 1: h5ad if cell_feature_matrix.h5 present."""
    path = Path(path)
    h5_candidates = list(path.rglob("cell_feature_matrix.h5")) + list(path.rglob("*.h5ad"))
    if h5_candidates:
        adata, meta = ingest_h5ad(h5_candidates[0])
        meta["platform"] = "xenium"
        meta["phase"] = "1-fallback-h5ad"
        meta["note"] = "Full Xenium parser planned Phase 2"
        return adata, meta
    raise NotImplementedError("Xenium full loader is Phase 2 — provide h5ad or cell_feature_matrix.h5")
