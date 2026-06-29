"""Spatial analysis workflow — Seurat-like pipeline integration."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule
from mbsi.profiles.scalability import scalability_mode, SCALABILITY_CONFIG


def run_analyze_workflow(adata: Any, params: Optional[Dict[str, Any]] = None) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.SPATIAL_ANALYSIS.value, "no AnnData loaded")
    params = params or {}
    warnings = []
    mode = scalability_mode(adata.n_obs)
    if mode != "in_memory":
        warnings.append(SCALABILITY_CONFIG["large_dataset_message"])

    try:
        from mbsi.analysis.seurat_like import run_seurat_like_pipeline

        results = run_seurat_like_pipeline(
            adata,
            preset=params.get("workflow_preset", "spatial_transcriptomics"),
            min_counts=params.get("min_counts", 500),
            min_genes=params.get("min_genes", 200),
            max_mito=params.get("max_mito", 25.0),
            n_top_genes=params.get("n_top_genes"),
            n_comps=params.get("n_comps"),
            n_neighbors=params.get("n_neighbors"),
            n_pcs=params.get("n_pcs"),
            resolution=params.get("resolution"),
            clustering_method=params.get("clustering_method", "Leiden"),
            normalization=params.get("normalization"),
        )
        warnings.extend(results.get("warnings", []))
        out_adata = results["adata"]
        return RunRecord.success(
            module=WorkflowModule.SPATIAL_ANALYSIS.value,
            inputs=params,
            outputs={
                "n_obs": out_adata.n_obs,
                "n_vars": out_adata.n_vars,
                "n_clusters": out_adata.obs["cluster"].nunique() if "cluster" in out_adata.obs else None,
                "has_spatial": "spatial" in out_adata.obsm,
                "scalability_mode": mode,
                "seurat_like_results": results,
                "status": "analysis_complete",
            },
            warnings=warnings,
        )
    except Exception as exc:
        return RunRecord.failed(
            WorkflowModule.SPATIAL_ANALYSIS.value,
            str(exc),
        )
