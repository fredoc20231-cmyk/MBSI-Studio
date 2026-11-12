"""Reproducible tissue-level Visium/spot expression QC, no hidden filtering.

Works for any AnnData expression table, but distinguishes raw counts from
normalized expression. Unit type is taken from metadata, never inferred.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def spatial_qc_summary(adata) -> dict:
    if adata.n_obs < 1 or adata.n_vars < 1:
        raise ValueError("Nonempty expression matrix required")
    layer = "counts" if "counts" in adata.layers else None
    matrix = adata.layers[layer] if layer else adata.X
    if sparse.issparse(matrix):
        n_detected = np.asarray((matrix != 0).getnnz(axis=1), dtype=float)
        totals = np.asarray(matrix.sum(axis=1)).reshape(-1).astype(float)
        values = matrix.data
    else:
        arr = np.asarray(matrix)
        n_detected = np.count_nonzero(arr, axis=1).astype(float)
        totals = np.asarray(arr.sum(axis=1), dtype=float)
        values = arr.ravel()
    if not np.isfinite(values).all() or not np.isfinite(totals).all():
        raise ValueError("Expression matrix contains nonfinite values")
    nonnegative_integer = (np.all(values >= 0)
                           and np.allclose(values, np.rint(values)))
    is_raw_counts = bool(nonnegative_integer)
    if layer is not None and not is_raw_counts:
        raise ValueError("adata.layers['counts'] is not a valid nonnegative integer count matrix")
    result = {
        "n_observations": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "assay": str(adata.uns.get("mbsi_platform", "unspecified")),
        "matrix_source": "layers.counts" if layer else "X",
        "matrix_is_integer_counts": is_raw_counts,
        "measurement_label": "counts" if is_raw_counts else "expression_units",
        "detected_features_per_observation": {
            "median": float(np.median(n_detected)),
            "q25": float(np.quantile(n_detected, 0.25)),
            "q75": float(np.quantile(n_detected, 0.75)),
        },
        "total_expression_per_observation": {
            "median": float(np.median(totals)),
            "q25": float(np.quantile(totals, 0.25)),
            "q75": float(np.quantile(totals, 0.75)),
        },
        "warnings": [],
    }
    if "in_tissue" in adata.obs:
        values = adata.obs["in_tissue"].fillna(False).astype(bool)
        result["in_tissue_fraction"] = float(values.mean())
    if not is_raw_counts:
        result["warnings"].append(
            "Matrix is not raw integer counts; totals are expression-scale sums, not UMI counts."
        )
    if "spatial" not in adata.obsm:
        result["warnings"].append("Spatial coordinates missing.")
    result["warnings"].append(
        "No automatic filtering, threshold selection, image registration or biological inference performed."
    )
    return result
