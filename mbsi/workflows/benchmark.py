"""Benchmark hub workflow."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_benchmark_workflow(
    adata: Any = None,
    ground_truth: Any = None,
    params: Optional[Dict[str, Any]] = None,
) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.BENCHMARK.value, "no spatial data loaded")
    if ground_truth is None and adata.uns.get("single_cell_reference") is None:
        return RunRecord.failed(
            WorkflowModule.BENCHMARK.value,
            "ground-truth reference required",
            inputs=params or {},
        )
    return RunRecord.success(
        module=WorkflowModule.BENCHMARK.value,
        inputs=params or {},
        outputs={"status": "delegate_to_benchmark_hub"},
    )
