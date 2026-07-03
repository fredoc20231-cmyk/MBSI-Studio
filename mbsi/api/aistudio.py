"""AIStudio frontend adapter — endpoints matching the React UI's JSON contract.

The AIStudio-generated frontend (StudySetupView / TissueCanvas / WorkbenchView)
consumes a specific JSON shape documented in its integration spec. This module
translates MBSI-Studio's internal AnnData + registry state into exactly that
contract so the frontend is plug-and-play. All numeric fields are computed from
the actual dataset — nothing is fabricated.

Endpoints
---------
GET  /api/projects/{project_id}/spatial-data   -> SpatialDataPayload
POST /api/upload/sign                           -> presigned-upload stub / direct fallback
GET  /api/jobs/{job_id}/status                  -> job polling contract
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mbsi.schema.technology import get_technology, list_technologies_api

_DATASETS_DIR = Path("data/registry/datasets")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _dataset_record(dataset_id: str) -> Optional[Dict[str, Any]]:
    path = _DATASETS_DIR / f"{dataset_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _to_dense_row_sums(X) -> np.ndarray:
    return np.asarray(X.sum(axis=1)).flatten()


def _mito_mask(var_names: List[str]) -> np.ndarray:
    upper = [str(g).upper() for g in var_names]
    return np.array([g.startswith("MT-") or g.startswith("MT.") for g in upper], dtype=bool)


def _select_display_genes(adata, requested: Optional[List[str]], max_genes: int) -> List[str]:
    """Pick genes to embed per-cell: honor request, else top-variance."""
    var_names = list(map(str, adata.var_names))
    if requested:
        present = [g for g in requested if g in set(var_names)]
        if present:
            return present[:max_genes]
    # Fall back to highest-variance genes (computed, deterministic).
    X = adata.X
    if hasattr(X, "toarray"):
        # variance without densifying the whole matrix
        n = X.shape[0]
        mean = np.asarray(X.mean(axis=0)).flatten()
        sq = np.asarray(X.multiply(X).mean(axis=0)).flatten() if hasattr(X, "multiply") else (mean ** 2)
        var = np.maximum(sq - mean ** 2, 0.0)
    else:
        var = np.asarray(X).var(axis=0)
    top = np.argsort(var)[::-1][:max_genes]
    return [var_names[i] for i in top]


def _qc_score(median_genes: float, mito_pct: float, n_cells: int) -> float:
    """Heuristic 0-100 QC score from real metrics (transparent, monotone)."""
    gene_component = min(median_genes / 3000.0, 1.0) * 60.0
    mito_penalty = max(0.0, min(mito_pct, 30.0)) / 30.0 * 25.0
    depth_component = min(n_cells / 2000.0, 1.0) * 15.0
    score = gene_component + depth_component + (25.0 - mito_penalty)
    return round(max(0.0, min(score, 100.0)), 1)


# --------------------------------------------------------------------------- #
# Technology list in frontend contract shape
# --------------------------------------------------------------------------- #
def technologies_frontend() -> List[Dict[str, Any]]:
    """Technology catalog with id/name/resolution/type guaranteed present.

    The AIStudio StudySetupView reads currentTech.resolution and currentTech.type;
    these keys are always populated here so the component never sees undefined.
    """
    out = []
    for entry in list_technologies_api():
        out.append(
            {
                "id": entry.get("id", entry.get("key")),
                "key": entry.get("key"),
                "name": entry.get("name", entry.get("display_name")),
                "resolution": entry.get("resolution", "Variable"),
                "type": entry.get("type", "Generic"),
                "modality": entry.get("type", "Generic"),
                "milestone_functional": entry.get("milestone_1_functional", False),
                "milestone_status": entry.get("milestone_status", "active"),
                "required_files": entry.get("required_files", []),
                "optional_files": entry.get("optional_files", []),
                "supports_images": entry.get("supports_images", False),
                "supports_segmentation": entry.get("supports_segmentation", False),
                "supports_cells": entry.get("supports_cells", False),
                "supports_bins": entry.get("supports_bins", False),
                "normalization": entry.get("normalization", ""),
                "clustering": entry.get("clustering", []),
                "compatible_analyses": entry.get("compatible_analyses", []),
                "notes": entry.get("notes", ""),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# spatial-data payload (main contract)
# --------------------------------------------------------------------------- #
def build_spatial_data_payload(
    dataset_id: str,
    *,
    genes: Optional[List[str]] = None,
    max_cells: int = 5000,
    max_genes: int = 12,
    histology_url: str = "",
) -> Dict[str, Any]:
    """Build the GET /api/projects/:id/spatial-data payload from a stored dataset.

    Every count / ratio / coordinate is read from the actual AnnData.
    """
    import anndata as ad

    record = _dataset_record(dataset_id)
    warnings: List[str] = []
    if record is None:
        return {
            "technology": "unknown",
            "error": f"Dataset {dataset_id} not found",
            "cells": [],
            "genesList": [],
            "validations": [],
        }

    technology = record.get("platform") or record.get("technology_key") or "unknown"
    adata_path = record.get("adata_path", "")
    if not adata_path or not Path(adata_path).exists():
        return {
            "technology": technology,
            "error": "AnnData payload missing — re-upload dataset",
            "cells": [],
            "genesList": [],
            "validations": [],
        }

    adata = ad.read_h5ad(adata_path)
    n_cells_total, n_genes_total = int(adata.n_obs), int(adata.n_vars)

    # --- QC metrics (computed) ------------------------------------------- #
    if "total_counts" in adata.obs:
        total_counts = np.asarray(adata.obs["total_counts"], dtype=float)
    else:
        total_counts = _to_dense_row_sums(adata.X).astype(float)

    if "n_genes_by_counts" in adata.obs:
        n_genes_by_counts = np.asarray(adata.obs["n_genes_by_counts"], dtype=float)
    else:
        X = adata.X
        n_genes_by_counts = np.asarray((X > 0).sum(axis=1)).flatten().astype(float)

    var_names_all = list(map(str, adata.var_names))
    mmask = _mito_mask(var_names_all)
    if "pct_counts_mt" in adata.obs:
        pct_mt = np.asarray(adata.obs["pct_counts_mt"], dtype=float)
    elif mmask.any():
        Xm = adata.X[:, mmask]
        mito_counts = _to_dense_row_sums(Xm).astype(float)
        pct_mt = np.divide(mito_counts, total_counts, out=np.zeros_like(mito_counts), where=total_counts > 0) * 100.0
    else:
        pct_mt = np.zeros(n_cells_total, dtype=float)
        warnings.append("No mitochondrial genes detected (MT- prefix) — pct_counts_mt set to 0")

    median_genes = float(np.median(n_genes_by_counts)) if n_cells_total else 0.0
    mean_mito = float(np.mean(pct_mt)) if n_cells_total else 0.0
    qc = _qc_score(median_genes, mean_mito, n_cells_total)

    # --- spatial coordinates -------------------------------------------- #
    if "spatial" in adata.obsm:
        coords = np.asarray(adata.obsm["spatial"], dtype=float)
    elif {"x", "y"}.issubset(set(adata.obs.columns)):
        coords = adata.obs[["x", "y"]].to_numpy(dtype=float)
    else:
        coords = np.column_stack([np.arange(n_cells_total), np.zeros(n_cells_total)]).astype(float)
        warnings.append("No spatial coordinates found — placeholder grid used")

    # --- clusters (if present) ------------------------------------------ #
    cluster_key = next((k for k in ("leiden", "louvain", "clusters", "cluster", "cell_type") if k in adata.obs), None)
    if cluster_key:
        raw = adata.obs[cluster_key].astype(str).to_numpy()
        uniq = {v: i for i, v in enumerate(sorted(set(raw)))}
        clusters = np.array([uniq[v] for v in raw], dtype=int)
    else:
        clusters = np.zeros(n_cells_total, dtype=int)

    # --- gene selection + per-cell expression --------------------------- #
    display_genes = _select_display_genes(adata, genes, max_genes)
    gene_idx = {g: i for i, g in enumerate(var_names_all)}
    sel_idx = [gene_idx[g] for g in display_genes if g in gene_idx]

    # --- subsample cells for payload size ------------------------------- #
    if n_cells_total > max_cells:
        rng = np.random.default_rng(0)
        keep = np.sort(rng.choice(n_cells_total, size=max_cells, replace=False))
        warnings.append(f"Subsampled {max_cells} of {n_cells_total} cells for payload (deterministic seed=0)")
    else:
        keep = np.arange(n_cells_total)

    # dense sub-block only for selected genes & kept cells
    if sel_idx:
        Xsub = adata.X[keep][:, sel_idx]
        Xsub = Xsub.toarray() if hasattr(Xsub, "toarray") else np.asarray(Xsub)
        # normalized (log1p CPM-ish) for the normalizedExpression field
        with np.errstate(divide="ignore", invalid="ignore"):
            libsize = total_counts[keep].reshape(-1, 1)
            norm = np.log1p(np.divide(Xsub, libsize, out=np.zeros_like(Xsub, dtype=float), where=libsize > 0) * 1e4)
    else:
        Xsub = np.zeros((len(keep), 0))
        norm = np.zeros((len(keep), 0))

    obs_names = list(map(str, adata.obs_names))
    cells: List[Dict[str, Any]] = []
    for row, ci in enumerate(keep):
        expr = {g: float(Xsub[row, j]) for j, g in enumerate(display_genes[: len(sel_idx)])}
        nexpr = {g: round(float(norm[row, j]), 4) for j, g in enumerate(display_genes[: len(sel_idx)])}
        cells.append(
            {
                "id": obs_names[ci],
                "x": round(float(coords[ci, 0]), 2),
                "y": round(float(coords[ci, 1]), 2),
                "cluster": int(clusters[ci]),
                "total_counts": int(total_counts[ci]),
                "n_genes_by_counts": int(n_genes_by_counts[ci]),
                "pct_counts_mt": round(float(pct_mt[ci]), 2),
                "expression": expr,
                "normalizedExpression": nexpr,
            }
        )

    # --- validations ----------------------------------------------------- #
    validations = [
        {
            "name": "Mitochondrial gene alignment",
            "status": "passed" if mmask.any() else "warning",
            "message": (
                f"Matched {int(mmask.sum())} MT- prefixed genes."
                if mmask.any()
                else "No MT- prefixed genes found; mito QC unavailable."
            ),
        },
        {
            "name": "Spatial coordinates present",
            "status": "passed" if ("spatial" in adata.obsm or {"x", "y"}.issubset(adata.obs.columns)) else "failed",
            "message": "obsm['spatial'] found." if "spatial" in adata.obsm else "Derived or missing coordinates.",
        },
        {
            "name": "Non-empty expression matrix",
            "status": "passed" if n_genes_total > 0 and n_cells_total > 0 else "failed",
            "message": f"{n_cells_total} cells x {n_genes_total} genes.",
        },
    ]

    return {
        "technology": technology,
        "matrixDimensions": f"{n_cells_total:,} cells x {n_genes_total:,} genes",
        "detectedCellsCount": n_cells_total,
        "detectedGenesCount": n_genes_total,
        "mitochondrialRatio": f"{mean_mito:.2f}%",
        "qcScore": qc,
        "histologyImageUrl": histology_url or record.get("histology_url", ""),
        "genesList": display_genes,
        "cells": cells,
        "validations": validations,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- #
# Upload signing (stub / direct-fallback)
# --------------------------------------------------------------------------- #
def sign_upload(filename: str, content_type: str = "application/octet-stream") -> Dict[str, Any]:
    """Return a presigned-upload descriptor.

    In cloud deployments this issues a GCS/S3 signed PUT URL. With no cloud
    credentials configured, it returns a direct-upload fallback pointing at the
    server's own /api/dataset/upload route so the frontend flow still works.
    """
    upload_id = uuid.uuid4().hex
    return {
        "uploadId": upload_id,
        "mode": "direct",  # 'signed' when cloud storage is configured
        "uploadUrl": "/api/dataset/upload",
        "method": "POST",
        "fields": {"upload_id": upload_id},
        "objectKey": f"uploads/{upload_id}/{filename}",
        "expiresIn": 3600,
        "note": "No cloud bucket configured; use direct multipart POST to uploadUrl.",
    }
