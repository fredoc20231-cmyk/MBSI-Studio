"""MBSI reconstruction workflow."""

from __future__ import annotations

from typing import Any, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_reconstruct_workflow(adata: Any, seed: int = 42) -> RunRecord:
    if adata is None:
        return RunRecord.failed(WorkflowModule.RECONSTRUCTION.value, "no AnnData loaded")
    if "spatial" not in adata.obsm:
        return RunRecord.failed(WorkflowModule.RECONSTRUCTION.value, "spatial coordinates required")
    return RunRecord.success(
        module=WorkflowModule.RECONSTRUCTION.value,
        inputs={"seed": seed, "n_obs": adata.n_obs},
        outputs={"status": "delegate_to_reconstruction_solver"},
    )
