"""Reproducible descriptive comparisons of annotated spatial AnnData samples.

This module never performs inferential DE, forcibly aligns clusters, or claims
independent biological replication from multiple cells within one section.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse


def _labels(adata, key: str) -> pd.Series:
    if key not in adata.obs:
        raise ValueError(f"Missing annotation column: {key}")
    result = adata.obs[key].astype("string").fillna("Unassigned").astype(str)
    if not len(result):
        raise ValueError("Sample has no observations")
    return result.reset_index(drop=True)


def _expression(adata, genes: list[str], layer: str | None = None) -> np.ndarray:
    if layer is not None and layer not in adata.layers:
        raise ValueError(f"Expression layer not found: {layer}")
    matrix = adata[:, genes].layers[layer] if layer else adata[:, genes].X
    if sparse.issparse(matrix):
        matrix = matrix.toarray()
    values = np.asarray(matrix, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Expression contains NaN or infinity")
    return values


def summarize_sample(adata, sample_id: str, label_key: str, genes: list[str],
                     layer: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return population counts and within-population mean expression."""
    labels = _labels(adata, label_key)
    if not adata.var_names.is_unique:
        raise ValueError("Gene identifiers must be unique")
    values = _expression(adata, genes, layer)
    summary = labels.value_counts(dropna=False).rename_axis("population").reset_index(name="n_units")
    summary["sample_id"] = sample_id
    summary["fraction"] = summary["n_units"] / len(labels)
    expressions = []
    for name in summary["population"]:
        mask = labels.to_numpy() == name
        for gene, mean in zip(genes, values[mask].mean(axis=0)):
            expressions.append({
                "sample_id": sample_id, "population": name,
                "gene": gene, "mean_expression": float(mean),
                "n_units": int(mask.sum()),
            })
    return summary[["sample_id", "population", "n_units", "fraction"]], pd.DataFrame(expressions)


def compare_samples(left, right, *, left_id="Sample A", right_id="Sample B",
                    left_label="cell_type", right_label="cell_type",
                    layer: str | None = None, max_genes: int = 2000) -> dict:
    """Compare matching *annotation names*; labels must have compatible meaning.

    Samples are not batch-corrected or statistically contrasted. Fold differences
    are descriptive differences of means in the selected expression space.
    """
    if left_id == right_id:
        raise ValueError("Sample names must be distinct")
    if left.n_obs == 0 or right.n_obs == 0:
        raise ValueError("Both samples must contain observations")
    if not left.var_names.is_unique or not right.var_names.is_unique:
        raise ValueError("Gene identifiers must be unique")
    common = sorted(set(map(str, left.var_names)) & set(map(str, right.var_names)))
    if not common:
        raise ValueError("Samples do not share gene identifiers")
    if len(common) > max_genes:
        raise ValueError(
            f"{len(common)} shared genes exceed preview limit {max_genes}. "
            "Filter to a gene panel before descriptive comparison."
        )
    if layer and (layer not in left.layers or layer not in right.layers):
        raise ValueError(f"Layer {layer} must exist in both samples")
    a, ax = summarize_sample(left, left_id, left_label, common, layer)
    b, bx = summarize_sample(right, right_id, right_label, common, layer)
    composition = a.merge(
        b, on="population", how="outer", suffixes=("_a", "_b")
    ).fillna({"n_units_a": 0, "n_units_b": 0, "fraction_a": 0.0, "fraction_b": 0.0})
    composition["delta_fraction"] = composition["fraction_b"] - composition["fraction_a"]
    # Report only populations annotated in both datasets. Unmatched stay in composition.
    means = ax.merge(bx, on=["population", "gene"], how="inner", suffixes=("_a", "_b"))
    means["delta_mean"] = means["mean_expression_b"] - means["mean_expression_a"]
    warnings = [
        "Exploratory/descriptive comparison only: no biological replicate-level significance tests.",
        "Population labels are compared by exact name; verify annotation equivalence.",
        "Expression means are not cross-platform harmonized; compare only compatible expression scales.",
        "A difference in cell/spot fractions does not prove differential abundance across patients.",
    ]
    if len(common) < 50:
        warnings.append("Limited shared gene panel; interpretation may be unreliable.")
    if left_label != right_label:
        warnings.append("Different annotation keys selected; confirm that their names mean the same thing.")
    return {
        "composition": composition.sort_values("population").reset_index(drop=True),
        "expression": means.sort_values(["population", "gene"]).reset_index(drop=True),
        "shared_genes": common,
        "warnings": warnings,
        "sample_ids": [left_id, right_id],
        "annotation_keys": [left_label, right_label],
        "status": "descriptive",
    }


def spatial_coordinates(adata) -> np.ndarray | None:
    """Return validated 2-D spatial coordinates, or None if not available."""
    if "spatial" not in adata.obsm:
        return None
    points = np.asarray(adata.obsm["spatial"])
    if points.ndim != 2 or points.shape[0] != adata.n_obs or points.shape[1] < 2:
        return None
    result = points[:, :2].astype(float)
    if not np.isfinite(result).all():
        return None
    return result
