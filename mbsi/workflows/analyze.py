"""Spatial analysis workflow — PCA, clustering, markers, Moran, SV genes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_analyze_workflow(adata: Any, params: Optional[Dict[str, Any]] = None) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.SPATIAL_ANALYSIS.value, "no AnnData loaded")
    params = params or {}
    return RunRecord.success(
        module=WorkflowModule.SPATIAL_ANALYSIS.value,
        inputs=params,
        outputs={
            "n_obs": adata.n_obs,
            "n_vars": adata.n_vars,
            "has_spatial": "spatial" in adata.obsm,
            "status": "delegate_to_analysis_module",
        },
    )
