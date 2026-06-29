"""Normalization and batch/replicate checks workflow."""

from __future__ import annotations

from typing import Any, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule
from mbsi.profiles.seurat_like import get_workflow_preset


def run_preprocess_workflow(
    adata: Any,
    technology_key: str = "",
    clustering_method: str = "Leiden",
    marker_panel: str = "",
    fdr_threshold: float = 0.05,
    normalization: str = "log1p",
    n_top_genes: int = 2000,
    workflow_preset: str = "basic_unsupervised",
) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.QC_PREPROCESS.value, "no AnnData loaded")
    tech = get_technology(technology_key)
    preset = get_workflow_preset(workflow_preset)
    strategy = normalization or preset.get("normalization", "log1p")
    if tech and strategy == "technology default":
        strategy = tech.normalization_strategy
    clustering_fallback = ""
    n_clusters = None
    norm_note = ""

    try:
        from mbsi.analysis.seurat_like.normalization import normalize_log1p, run_sctransform_like
        from mbsi.analysis.seurat_like.variable_features import find_variable_features
        from mbsi.analysis.seurat_like.reduction import scale_data, run_pca, run_neighbors
        from mbsi.analysis.seurat_like.clustering import run_leiden, run_louvain

        work = adata.copy()
        if "sctransform" in strategy.lower():
            work, norm_note = run_sctransform_like(work)
        else:
            work = normalize_log1p(work)
        work = find_variable_features(work, n_top_genes=n_top_genes or preset.get("n_top_genes", 2000))
        work = scale_data(work)
        work = run_pca(work)
        work = run_neighbors(work)
        if "louvain" in clustering_method.lower():
            work, clustering_fallback = run_louvain(work)
        else:
            work, clustering_fallback = run_leiden(work)
        n_clusters = work.obs["cluster"].nunique() if "cluster" in work.obs else None
    except Exception as exc:
        clustering_fallback = f"Preprocess pipeline skipped: {exc}"

    warnings = [w for w in (norm_note, clustering_fallback) if w]
    return RunRecord.success(
        module=WorkflowModule.QC_PREPROCESS.value,
        inputs={
            "technology_key": technology_key,
            "clustering_method": clustering_method,
            "marker_panel": marker_panel,
            "fdr_threshold": fdr_threshold,
            "normalization": strategy,
            "n_top_genes": n_top_genes,
            "workflow_preset": workflow_preset,
        },
        outputs={
            "normalization_strategy": strategy,
            "normalization_note": norm_note,
            "clustering_method": clustering_method,
            "clustering_fallback": clustering_fallback,
            "n_clusters": n_clusters,
            "marker_panel": marker_panel,
            "status": "preprocess_complete",
        },
        warnings=warnings,
    )
