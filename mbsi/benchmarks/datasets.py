"""Ground-truth dataset loading and validation for Benchmark Hub."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import anndata as ad
import numpy as np
import pandas as pd


REQUIRED_OBS_KEYS = ("cell_type",)
RECOMMENDED_UNS = ("platform",)


def validate_single_cell_spatial_ground_truth(adata: ad.AnnData) -> Dict[str, Any]:
    """
    Validate AnnData for benchmark ground truth.

    Returns readiness dict with score 0-100 and checklist.
    """
    checks = []
    score = 0

    if adata.n_obs >= 20:
        checks.append(("min_cells", True, f"{adata.n_obs} cells"))
        score += 20
    else:
        checks.append(("min_cells", False, f"Only {adata.n_obs} cells (need ≥20)"))

    if adata.n_vars >= 10:
        checks.append(("min_genes", True, f"{adata.n_vars} genes"))
        score += 15
    else:
        checks.append(("min_genes", False, f"Only {adata.n_vars} genes"))

    if "spatial" in adata.obsm and adata.obsm["spatial"].shape[1] >= 2:
        checks.append(("spatial_coords", True, "obsm['spatial'] present"))
        score += 25
    else:
        checks.append(("spatial_coords", False, "Missing obsm['spatial']"))

    has_labels = any(k in adata.obs.columns for k in ("cell_type", "label", "compartment"))
    if has_labels:
        checks.append(("cell_labels", True, "cell_type/label present"))
        score += 20
    else:
        checks.append(("cell_labels", False, "No cell_type or label column"))

    if adata.X is not None and np.asarray(adata.X.sum() if hasattr(adata.X, "sum") else adata.X).sum() > 0:
        checks.append(("expression", True, "Non-zero expression matrix"))
        score += 20
    else:
        checks.append(("expression", False, "Empty expression matrix"))

    return {
        "readiness_score": min(100, score),
        "ready": score >= 60,
        "checks": [{"name": c[0], "pass": c[1], "detail": c[2]} for c in checks],
        "n_cells": adata.n_obs,
        "n_genes": adata.n_vars,
    }


def load_ground_truth_dataset(path: Union[str, Path]) -> ad.AnnData:
    """Load ground truth from h5ad or CSV+coords bundle."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() in (".h5ad", ".h5"):
        return ad.read_h5ad(path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, index_col=0)
        adata = ad.AnnData(X=df.values.astype(np.float32))
        adata.var_names = df.columns.astype(str)
        adata.obs_names = df.index.astype(str)
        coords_path = path.with_name(path.stem + "_coords.csv")
        if coords_path.exists():
            coords = pd.read_csv(coords_path)
            adata.obsm["spatial"] = coords[["x", "y"]].values.astype(np.float32)
        return adata

    raise ValueError(f"Unsupported format: {path.suffix}")


def prepare_ground_truth_for_benchmark(adata: ad.AnnData) -> ad.AnnData:
    """Normalize ground truth AnnData for benchmarking."""
    adata = adata.copy()
    if "spatial" not in adata.obsm:
        if "x" in adata.obs.columns and "y" in adata.obs.columns:
            adata.obsm["spatial"] = adata.obs[["x", "y"]].values.astype(np.float32)
        else:
            raise ValueError("Ground truth requires obsm['spatial'] or obs x/y columns")

    if "cell_type" not in adata.obs.columns:
        if "label" in adata.obs.columns:
            adata.obs["cell_type"] = adata.obs["label"].astype(str)
        elif "compartment" in adata.obs.columns:
            adata.obs["cell_type"] = adata.obs["compartment"].astype(str)

    if "logcounts" not in adata.layers:
        X = adata.X
        if hasattr(X, "toarray"):
            X = X.toarray()
        totals = np.asarray(X).sum(axis=1, keepdims=True) + 1e-12
        adata.layers["logcounts"] = np.log1p(np.asarray(X) / totals * 1e4)

    adata.uns.setdefault("benchmark_prepared", True)
    return adata
