"""Exploratory rectangular ROI summaries on a single tissue section.

An ROI is expressed in the coordinate system of the uploaded AnnData.
It does not imply registration between different tissue sections.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from .preview import spatial_coordinates


def roi_summary(adata, *, xmin: float, xmax: float, ymin: float, ymax: float,
                annotation: str, genes: list[str]) -> dict:
    if xmin >= xmax or ymin >= ymax:
        raise ValueError("ROI requires xmin < xmax and ymin < ymax")
    coords = spatial_coordinates(adata)
    if coords is None:
        raise ValueError("ROI requires finite spatial coordinates")
    if annotation not in adata.obs:
        raise ValueError("Unknown annotation")
    if not genes or len(genes) > 100:
        raise ValueError("ROI requires between 1 and 100 genes")
    if not set(genes).issubset(set(adata.var_names)):
        raise ValueError("ROI genes must exist in the dataset")
    inside = ((coords[:, 0] >= xmin) & (coords[:, 0] <= xmax)
              & (coords[:, 1] >= ymin) & (coords[:, 1] <= ymax))
    n = int(inside.sum())
    if n == 0:
        return {"n_units": 0, "fraction_of_tissue": 0.0,
                "composition": [], "expression": [],
                "warnings": ["No observations within the chosen ROI."]}
    labels = adata.obs[annotation].astype("string").fillna("Unassigned").astype(str)
    comp = labels.iloc[np.flatnonzero(inside)].value_counts()
    matrix = adata[inside, genes].X
    means = np.asarray(matrix.mean(axis=0)).ravel() if sparse.issparse(matrix) else np.asarray(matrix).mean(axis=0)
    return {
        "n_units": n,
        "fraction_of_tissue": float(n / adata.n_obs),
        "composition": [
            {"population": str(name), "n_units": int(count), "fraction": float(count / n)}
            for name, count in comp.items()
        ],
        "expression": [{"gene": gene, "mean_expression": float(mean)} for gene, mean in zip(genes, means)],
        "warnings": [
            "ROI summary is descriptive; no spatial null model or independent biological replication.",
            "Bounding rectangle uses source dataset coordinates; no cross-tissue registration.",
            "Gene means use the supplied .X expression scale.",
        ],
    }
