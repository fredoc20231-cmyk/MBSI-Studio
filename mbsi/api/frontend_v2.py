"""Lovable / React-friendly API for real spatial data (local research mode).

No synthetic records, arbitrary filesystem paths, or inferential p-values.
Use the existing upload endpoint for ingest and validated dataset IDs.
Production exposure requires authentication, rate limits and object storage.
"""
from __future__ import annotations

import re
from typing import Literal

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mbsi.api import handlers
from mbsi.comparative import compare_samples, spatial_coordinates
from mbsi.comparative.cluster_matching import cluster_similarity

router = APIRouter(prefix="/api/v2", tags=["MBSI Studio frontend"])

_ID = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def _get(dataset_id: str):
    if not _ID.fullmatch(dataset_id):
        raise HTTPException(status_code=422, detail="Invalid dataset identifier")
    adata, warnings = handlers._load_adata_for_dataset(dataset_id)
    if adata is None:
        raise HTTPException(status_code=404, detail="Dataset unavailable: " + "; ".join(warnings))
    return adata


def _annotations(adata):
    from pandas.api.types import is_categorical_dtype, is_object_dtype, is_string_dtype
    return [
        str(k) for k in adata.obs.columns
        if (is_categorical_dtype(adata.obs[k])
            or is_object_dtype(adata.obs[k])
            or is_string_dtype(adata.obs[k]))
        and 1 <= adata.obs[k].nunique() <= 100
    ]


class ComparisonRequest(BaseModel):
    reference_dataset_id: str = Field(min_length=1, max_length=128)
    comparison_dataset_id: str = Field(min_length=1, max_length=128)
    reference_annotation: str = Field(min_length=1, max_length=128)
    comparison_annotation: str = Field(min_length=1, max_length=128)
    genes: list[str] = Field(min_length=1, max_length=100)
    include_similarity: bool = True


@router.get("/capabilities")
def capabilities():
    return {
        "product": "MBSI Studio",
        "api_version": "2.0-preview",
        "mode": "local_research",
        "real_data_only": True,
        "supports": {
            "visium_v1_v2": "existing_ingestion",
            "xenium": "existing_ingestion",
            "h5ad": "existing_ingestion_and_comparisons",
            "visium_hd": "adapter_required",
            "cosmx": "experimental_adapter",
            "merfish": "experimental_adapter",
            "comparative_descriptive": "preview",
            "statistical_inference": "not_implemented_in_v2_preview",
            "histology_tiles": "not_implemented_in_v2_preview",
        },
        "requirements": [
            "Use POST /api/dataset/upload for actual datasets",
            "Never present experimental features as measured results",
            "Do not expose this local API publicly without authentication",
        ],
    }


@router.get("/datasets/{dataset_id}/summary")
def dataset_summary(dataset_id: str):
    a = _get(dataset_id)
    return {
        "dataset_id": dataset_id,
        "observations": int(a.n_obs),
        "genes": int(a.n_vars),
        "annotation_columns": _annotations(a),
        "spatial_available": spatial_coordinates(a) is not None,
        "platform": str(a.uns.get("mbsi_platform", "unknown")),
        "expression_space": "adata.X; verify matching normalization across samples",
    }


@router.get("/datasets/{dataset_id}/genes")
def dataset_genes(
    dataset_id: str,
    query: str = Query(default="", max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
):
    a = _get(dataset_id)
    # Bounded search so the frontend does not request whole transcriptomes.
    q = query.casefold().strip()
    names = [str(g) for g in a.var_names if not q or q in str(g).casefold()]
    return {"dataset_id": dataset_id, "genes": names[:limit], "total_matches": len(names)}


@router.get("/datasets/{dataset_id}/spatial-points")
def spatial_points(
    dataset_id: str,
    annotation: str = Query(..., min_length=1, max_length=128),
    gene: str | None = Query(default=None, max_length=128),
    limit: int = Query(default=10000, ge=1, le=50000),
):
    a = _get(dataset_id)
    coords = spatial_coordinates(a)
    if coords is None:
        raise HTTPException(status_code=422, detail="No valid spatial coordinates")
    if annotation not in a.obs:
        raise HTTPException(status_code=422, detail="Unknown annotation")
    if gene is not None and gene not in a.var_names:
        raise HTTPException(status_code=422, detail="Unknown gene")
    # Deterministic even sampling; capped JSON payload. Tile streaming is future work.
    selected = np.linspace(0, a.n_obs - 1, min(limit, a.n_obs), dtype=int)
    labels = a.obs[annotation].astype("string").fillna("Unassigned").astype(str).to_numpy()
    expr = None
    if gene:
        from scipy import sparse
        arr = a[:, [gene]].X
        expr = np.asarray(arr.toarray() if sparse.issparse(arr) else arr).ravel()
        if not np.isfinite(expr[selected]).all():
            raise HTTPException(status_code=422, detail="Nonfinite gene expression")
    points = [
        {"x": float(coords[i, 0]), "y": float(coords[i, 1]),
         "annotation": labels[i],
         **({"expression": float(expr[i])} if expr is not None else {})}
        for i in selected
    ]
    return {
        "dataset_id": dataset_id, "annotation": annotation, "gene": gene,
        "observation_count": int(a.n_obs),
        "returned_count": len(points), "sampling": "deterministic_even_index",
        "coordinate_units": "source_dataset_units_unverified",
        "points": points,
    }


@router.post("/comparisons/preview")
def comparison_preview(request: ComparisonRequest):
    if request.reference_dataset_id == request.comparison_dataset_id:
        raise HTTPException(status_code=422, detail="Select two distinct datasets")
    a = _get(request.reference_dataset_id)
    b = _get(request.comparison_dataset_id)
    if not set(request.genes).issubset(set(a.var_names)) or not set(request.genes).issubset(set(b.var_names)):
        raise HTTPException(status_code=422, detail="Selected genes must exist in both datasets")
    try:
        result = compare_samples(
            a[:, request.genes].copy(), b[:, request.genes].copy(),
            left_id=request.reference_dataset_id,
            right_id=request.comparison_dataset_id,
            left_label=request.reference_annotation,
            right_label=request.comparison_annotation,
        )
        sim = None
        if request.include_similarity:
            try:
                matrix = cluster_similarity(
                    a, b, request.reference_annotation, request.comparison_annotation, request.genes
                )
                sim = {"reference_labels": list(matrix.index),
                       "comparison_labels": list(matrix.columns),
                       "values": matrix.to_numpy().tolist()}
            except ValueError as exc:
                result["warnings"].append("Similarity unavailable: " + str(exc))
        return {
            "status": "descriptive_only",
            "reference_dataset_id": request.reference_dataset_id,
            "comparison_dataset_id": request.comparison_dataset_id,
            "composition": result["composition"].to_dict(orient="records"),
            "expression": result["expression"].to_dict(orient="records"),
            "cluster_similarity": sim,
            "warnings": result["warnings"],
            "provenance": {
                "method": "mean expression and observed composition, with optional cosine signature similarity",
                "inference": "none",
                "normalization": "input data as provided",
                "comparison_unit": "annotated spots/cells, not independent subjects",
            },
        }
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
