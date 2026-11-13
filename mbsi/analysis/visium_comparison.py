"""Validated multi-sample Visium count-matrix comparison; no synthetic data."""
from __future__ import annotations

from collections.abc import Mapping
import numpy as np
import pandas as pd
import anndata as ad
from scipy import sparse


def combine_visium_samples(samples: Mapping[str, ad.AnnData]) -> ad.AnnData:
    """Combine raw-count samples on shared genes; retain sample-local spatial coordinates."""
    if len(samples) < 2:
        raise ValueError("At least two samples are required")
    prepared = {}
    for sample_id, source in samples.items():
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError("Sample IDs must be nonempty strings")
        if not isinstance(source, ad.AnnData) or not source.n_obs or not source.n_vars:
            raise ValueError(f"{sample_id}: nonempty AnnData required")
        coords = source.obsm.get("spatial")
        if coords is None or coords.shape != (source.n_obs, 2) or not np.isfinite(coords).all():
            raise ValueError(f"{sample_id}: finite Nx2 spatial coordinates required")
        if not source.var_names.is_unique:
            raise ValueError(f"{sample_id}: duplicate gene identifiers")
        x = source.X
        values = x.data if sparse.issparse(x) else np.asarray(x)
        if not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values, np.round(values)):
            raise ValueError(f"{sample_id}: expected nonnegative integer raw counts")
        sample = source.copy()
        sample.layers["counts"] = sample.X.copy()
        sample.obs["sample_id"] = sample_id
        prepared[sample_id] = sample
    shared = set.intersection(*(set(a.var_names) for a in prepared.values()))
    if not shared:
        raise ValueError("No shared genes across samples")
    genes = sorted(shared)
    prepared = {key: a[:, genes].copy() for key, a in prepared.items()}
    result = ad.concat(prepared, join="inner", label="sample_id", index_unique="::",
                       merge="same", uns_merge=None)
    result.uns["mbsi_multisample"] = {
        "sample_ids": list(prepared), "n_shared_genes": len(genes),
        "coordinate_policy": "sample-local: never overlay pooled coordinates on one image",
        "data_provenance": "observed raw counts"
    }
    return result


def per_sample_qc(adata: ad.AnnData) -> pd.DataFrame:
    """Observed spot counts and detected genes, grouped by sample."""
    if "sample_id" not in adata.obs or "counts" not in adata.layers:
        raise ValueError("Requires sample_id and raw counts layer")
    x = adata.layers["counts"]
    total = np.asarray(x.sum(axis=1)).ravel()
    detected = np.asarray((x > 0).sum(axis=1)).ravel()
    frame = pd.DataFrame({"sample_id": adata.obs["sample_id"].to_numpy(),
                          "total_counts": total, "detected_genes": detected})
    return frame.groupby("sample_id", observed=True).agg(
        n_spots=("total_counts", "size"),
        median_counts=("total_counts", "median"),
        median_detected_genes=("detected_genes", "median")).reset_index()


def compare_gene_expression(adata: ad.AnnData, gene: str) -> pd.DataFrame:
    """Descriptive comparison; does not imply patient-level statistical significance."""
    if gene not in adata.var_names:
        raise KeyError(f"Gene not found: {gene}")
    if "sample_id" not in adata.obs:
        raise ValueError("sample_id missing")
    sub = adata[:, [gene]]
    x = sub.layers["counts"] if "counts" in sub.layers else sub.X
    values = np.asarray(x.toarray() if sparse.issparse(x) else x).ravel()
    frame = pd.DataFrame({"sample_id": adata.obs["sample_id"].to_numpy(), "counts": values})
    return frame.groupby("sample_id", observed=True).agg(
        n_spots=("counts", "size"), mean_counts=("counts", "mean"),
        median_counts=("counts", "median"),
        detection_fraction=("counts", lambda x: float((x > 0).mean()))).reset_index()
