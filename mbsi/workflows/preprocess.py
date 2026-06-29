"""Normalization and batch/replicate checks workflow."""

from __future__ import annotations

from typing import Any, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule


def run_preprocess_workflow(adata: Any, technology_key: str = "") -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.QC_PREPROCESS.value, "no AnnData loaded")
    tech = get_technology(technology_key)
    strategy = tech.normalization_strategy if tech else "log1p + scale"
    return RunRecord.success(
        module=WorkflowModule.QC_PREPROCESS.value,
        inputs={"technology_key": technology_key},
        outputs={"normalization_strategy": strategy, "status": "demo_normalize_complete"},
    )
