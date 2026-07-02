"""Milestone 1 unified analysis pipeline — Visium, Xenium, Generic h5ad/CSV."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import pandas as pd

from mbsi.workflows.xenium_pipeline import (
    run_visium_milestone_pipeline,
    run_xenium_milestone_pipeline,
)


def run_milestone1_pipeline(
    adata: ad.AnnData,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run Milestone 1 scanpy-based pipeline (QC → normalize → PCA/UMAP → clusters → markers → spatial).

    Returns dict with keys: status, qc_summary, normalization, embedding, clusters, markers,
    spatial, warnings, adata, output_paths, platform.
    """
    params = dict(params or {})
    platform = (
        params.pop("platform", None)
        or adata.uns.get("mbsi_platform")
        or "generic_h5ad"
    )
    if platform == "csv_matrix":
        platform = "generic_h5ad"

    output_dir = Path(params.pop("output_dir", Path("data/outputs/milestone1_pipeline")))
    pipeline_kwargs = dict(params)

    if platform == "xenium":
        raw = run_xenium_milestone_pipeline(adata, output_dir, **pipeline_kwargs)
    else:
        filter_tissue = pipeline_kwargs.pop("filter_tissue", platform == "visium")
        raw = run_visium_milestone_pipeline(
            adata,
            output_dir,
            filter_tissue=filter_tissue,
            **pipeline_kwargs,
        )

    out_adata = raw["adata"]
    qc_summary = raw.get("qc_summary")
    if not isinstance(qc_summary, pd.DataFrame):
        qc_summary = pd.DataFrame()

    n_clusters = 0
    if "cluster" in out_adata.obs.columns:
        n_clusters = int(out_adata.obs["cluster"].nunique())

    norm_method = "log1p"
    if out_adata.uns.get("mbsi_normalization"):
        norm_method = str(out_adata.uns["mbsi_normalization"])
    elif out_adata.uns.get("log1p"):
        norm_method = "log1p"

    return {
        "status": "success",
        "qc_summary": qc_summary,
        "normalization": {
            "method": norm_method,
            "n_obs": out_adata.n_obs,
            "n_vars": out_adata.n_vars,
        },
        "embedding": {
            "has_pca": "X_pca" in out_adata.obsm,
            "has_umap": "X_umap" in out_adata.obsm,
            "n_pcs": int(out_adata.obsm["X_pca"].shape[1]) if "X_pca" in out_adata.obsm else 0,
        },
        "clusters": {
            "n_clusters": n_clusters,
            "key": "cluster" if "cluster" in out_adata.obs.columns else None,
        },
        "markers": raw.get("markers"),
        "spatial": {
            "has_spatial": "spatial" in out_adata.obsm,
            "spatial_plots": raw.get("spatial_plots", []),
            "spatial_stats": raw.get("spatial_stats"),
        },
        "warnings": list(raw.get("warnings") or []),
        "adata": out_adata,
        "output_paths": raw.get("output_paths", {}),
        "platform": platform,
        "squidpy": raw.get("squidpy"),
    }
