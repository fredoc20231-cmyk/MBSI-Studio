"""QC thresholds, mito/ribo, filtering workflow."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule


def run_qc_workflow(
    adata: Any,
    min_counts: int = 10,
    min_genes: int = 200,
    max_mito_pct: float = 20.0,
    technology_key: str = "",
    workflow_preset: str = "basic_unsupervised",
) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.QC_PREPROCESS.value, "no AnnData loaded")
    tech = get_technology(technology_key)
    platform_qc = list(tech.qc_metrics) if tech else []
    warnings = []

    try:
        from mbsi.analysis.seurat_like.qc import run_qc

        filtered, qc_summary, qc_warnings = run_qc(
            adata,
            min_counts=min_counts,
            min_genes=min_genes,
            max_mito=max_mito_pct,
        )
        warnings.extend(qc_warnings)
        n_obs = filtered.n_obs
        has_spatial = "spatial" in getattr(filtered, "obsm", {})
    except Exception as exc:
        n_obs = getattr(adata, "n_obs", 0)
        has_spatial = "spatial" in getattr(adata, "obsm", {})
        qc_summary = None
        warnings.append(f"Seurat-like QC fallback: {exc}")

    if not has_spatial:
        warnings.append("spatial coordinates missing")

    return RunRecord.success(
        module=WorkflowModule.QC_PREPROCESS.value,
        inputs={
            "min_counts": min_counts,
            "min_genes": min_genes,
            "max_mito_pct": max_mito_pct,
            "technology_key": technology_key,
            "workflow_preset": workflow_preset,
        },
        outputs={
            "n_obs": n_obs,
            "has_spatial": has_spatial,
            "platform_qc_metrics": platform_qc,
            "technology_label": tech.label if tech else technology_key,
            "qc_summary_rows": len(qc_summary) if qc_summary is not None and hasattr(qc_summary, "__len__") else 0,
            "status": "qc_complete",
        },
        warnings=warnings,
    )
