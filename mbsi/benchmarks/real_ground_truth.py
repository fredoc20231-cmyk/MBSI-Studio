"""Real ground-truth dataset helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad

from mbsi.benchmarks.datasets import (
    validate_single_cell_spatial_ground_truth,
    load_ground_truth_dataset,
    prepare_ground_truth_for_benchmark,
)
from mbsi.benchmarks.pseudo_visium import make_synthetic_ground_truth


def resolve_ground_truth_adata(
    mode: str = "synthetic",
    uploaded_path: Optional[str] = None,
    session_adata: Optional[ad.AnnData] = None,
    seed: int = 42,
    n_cells: int = 200,
) -> tuple[ad.AnnData, Dict[str, Any]]:
    """
    Resolve ground truth by dataset mode.

    Modes: synthetic, upload, session
    """
    meta = {"mode": mode, "source": mode}

    if mode == "upload" and uploaded_path:
        adata = load_ground_truth_dataset(uploaded_path)
        meta["source"] = uploaded_path
    elif mode == "session" and session_adata is not None:
        adata = session_adata.copy()
        meta["source"] = "session_state"
    else:
        adata = make_synthetic_ground_truth(n_cells=n_cells, seed=seed)
        meta["mode"] = "synthetic"
        meta["source"] = f"synthetic_seed_{seed}"

    adata = prepare_ground_truth_for_benchmark(adata)
    validation = validate_single_cell_spatial_ground_truth(adata)
    meta["validation"] = validation
    return adata, meta
