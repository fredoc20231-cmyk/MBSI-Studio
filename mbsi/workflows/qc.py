"""QC thresholds, mito/ribo, filtering workflow."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_qc_workflow(
    adata: Any,
    min_counts: int = 10,
    max_mito_pct: float = 20.0,
    technology_key: str = "",
) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.QC_PREPROCESS.value, "no AnnData loaded")
    n_obs = getattr(adata, "n_obs", 0)
    has_spatial = "spatial" in getattr(adata, "obsm", {})
    return RunRecord.success(
        module=WorkflowModule.QC_PREPROCESS.value,
        inputs={"min_counts": min_counts, "max_mito_pct": max_mito_pct, "technology_key": technology_key},
        outputs={
            "n_obs": n_obs,
            "has_spatial": has_spatial,
            "status": "demo_qc_complete",
        },
        warnings=[] if has_spatial else ["spatial coordinates missing"],
    )
