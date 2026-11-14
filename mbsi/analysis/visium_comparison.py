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


def pseudobulk_counts(
    adata: ad.AnnData,
    *,
    group_keys: tuple[str, ...] = ("sample_id",),
    min_spots: int = 1,
) -> tuple[ad.AnnData, pd.DataFrame]:
    """Sum observed raw spot counts per biological unit, not per-spot pseudo-replicates.

    Pass group_keys such as ("patient_id", "condition") for patient-level units.
    This function produces aggregated counts only; it does not perform significance
    testing or infer independence of tissue sections from the same patient.
    """
    if not group_keys or min_spots < 1:
        raise ValueError("Specify group_keys and min_spots >= 1")
    absent = [key for key in group_keys if key not in adata.obs]
    if absent:
        raise ValueError(f"Missing metadata columns: {absent}")
    if "counts" not in adata.layers:
        raise ValueError("Raw counts layer is required for pseudobulk")
    x = adata.layers["counts"]
    values = x.data if sparse.issparse(x) else np.asarray(x)
    if not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values, np.round(values)):
        raise ValueError("Pseudobulk requires nonnegative integer raw counts")
    metadata = adata.obs.loc[:, list(group_keys)]
    if metadata.isna().any().any():
        raise ValueError("Grouping metadata contains missing values")
    grouped = metadata.groupby(list(group_keys), sort=True, observed=True, dropna=False).indices
    matrices, records = [], []
    for key, indices in grouped.items():
        if len(indices) < min_spots:
            continue
        key_values = (key,) if len(group_keys) == 1 else tuple(key)
        records.append({**dict(zip(group_keys, key_values)), "n_spots": len(indices)})
        matrices.append(sparse.csr_matrix(x[indices].sum(axis=0)))
    if not matrices:
        raise ValueError("No groups satisfy min_spots")
    obs = pd.DataFrame.from_records(records)
    obs.index = pd.Index(["unit_" + str(i) for i in range(len(obs))], name="unit_id")
    result = ad.AnnData(X=sparse.vstack(matrices, format="csr"), obs=obs,
                        var=adata.var.copy())
    result.layers["counts"] = result.X.copy()
    result.uns["mbsi_pseudobulk"] = {
        "group_keys": list(group_keys), "min_spots": min_spots,
        "statistical_note": "Aggregated counts; no independence or differential-expression claim"
    }
    return result, obs.copy()
