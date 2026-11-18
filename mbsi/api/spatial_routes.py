"""Read-only observed-data endpoints for Lovable spatial explorer.

Dataset IDs resolve only against the server registry. No filesystem paths,
synthetic values, clinical annotations, or full matrices are returned.
This API is for local development until authentication/tenancy is installed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import anndata as ad
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from scipy import sparse

router = APIRouter(prefix="/api/v1", tags=["spatial-explorer"])
_REGISTRY = Path("data/registry/datasets")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _record(dataset_id: str) -> dict:
    if not _ID.fullmatch(dataset_id):
        raise HTTPException(422, "Invalid dataset identifier")
    path = _REGISTRY / f"{dataset_id}.json"
    if not path.is_file():
        raise HTTPException(404, "Dataset not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, "Dataset registry record is invalid") from exc


def _open(dataset_id: str):
    record = _record(dataset_id)
    source = record.get("adata_path")
    if not source:
        raise HTTPException(409, "Dataset is not ingested as AnnData")
    # Only trust files within the server-owned ingestion directory.
    root = Path("data/registry/ingested").resolve()
    path = Path(source).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(409, "Dataset data path is unavailable")
    try:
        return ad.read_h5ad(path, backed="r")
    except (OSError, ValueError) as exc:
        raise HTTPException(409, "Dataset AnnData could not be opened") from exc


def _coordinates(a) -> np.ndarray:
    coords = a.obsm.get("spatial")
    if coords is None:
        raise HTTPException(409, "Dataset has no observed spatial coordinates")
    values = np.asarray(coords, dtype=float)
    if values.shape != (a.n_obs, 2) or not np.isfinite(values).all():
        raise HTTPException(409, "Dataset spatial coordinates are invalid")
    return values


@router.get("/datasets")
def datasets(project_id: str = Query(default="")):
    """List ingested datasets; never expose absolute server storage paths."""
    if not _REGISTRY.exists():
        return {"datasets": []}
    result = []
    for path in sorted(_REGISTRY.glob("*.json")):
        if not _ID.fullmatch(path.stem):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if project_id and record.get("project_id") != project_id:
            continue
        result.append({
            "dataset_id": path.stem,
            "sample_id": record.get("sample_id", ""),
            "project_id": record.get("project_id", ""),
            "platform": record.get("platform", "unknown"),
            "readiness": record.get("readiness", {}),
            "summary": {
                "n_obs": record.get("metadata", {}).get("n_obs", 0),
                "n_vars": record.get("metadata", {}).get("n_vars", 0),
            },
            "has_spatial_data": bool(record.get("adata_path")),
        })
    return {"datasets": result}


@router.get("/datasets/{dataset_id}/features")
def features(dataset_id: str, query: str = Query(default="", max_length=100),
             limit: int = Query(default=50, ge=1, le=200)):
    a = _open(dataset_id)
    try:
        genes = list(map(str, a.var_names))
        matched = [g for g in genes if query.casefold() in g.casefold()][:limit]
        annotations = [k for k in ("cluster", "leiden", "domain", "cell_type", "niche", "condition")
                       if k in a.obs.columns]
        return {"dataset_id": dataset_id, "genes": matched, "annotations": annotations,
                "total_genes": len(genes)}
    finally:
        a.file.close()


@router.get("/datasets/{dataset_id}/spatial")
def spatial(dataset_id: str, gene: str | None = Query(default=None, max_length=150),
            annotation: str | None = Query(default=None, max_length=150),
            limit: int = Query(default=5000, ge=1, le=10000)):
    """Bounded deterministic spot/cell scatter with explicit display sampling.

    Gene values are from AnnData.X, without implicit log transforms or
    cross-sample normalization. Never interpret this as a statistical test.
    """
    if bool(gene) == bool(annotation):
        raise HTTPException(422, "Specify exactly one gene or annotation")
    a = _open(dataset_id)
    try:
        coords = _coordinates(a)
        if gene:
            if gene not in a.var_names:
                raise HTTPException(404, "Gene not found")
            col = a[:, [gene]].X
            values = np.asarray(col.toarray() if sparse.issparse(col) else col).ravel()
            if not np.issubdtype(values.dtype, np.number) or not np.isfinite(values).all():
                raise HTTPException(409, "Expression contains non-finite values")
            category = False
        else:
            if annotation not in a.obs.columns:
                raise HTTPException(404, "Annotation not found")
            values = a.obs[annotation].astype(str).to_numpy()
            category = True
        n = int(a.n_obs)
        indexes = np.linspace(0, n - 1, min(n, limit), dtype=int) if n else np.array([], dtype=int)
        barcodes = np.asarray(a.obs_names.astype(str))
        points = [
            {"barcode": str(barcodes[i]), "x": float(coords[i, 0]),
             "y": float(coords[i, 1]),
             "value": str(values[i]) if category else float(values[i])}
            for i in indexes
        ]
        return {
            "dataset_id": dataset_id,
            "feature": annotation or gene,
            "categorical": category,
            "source_layer": "obs" if category else "X",
            "total_observations": n,
            "returned_observations": len(points),
            "downsampled": len(points) < n,
            "coordinate_system": "source_obsm_spatial",
            "points": points,
        }
    finally:
        a.file.close()
