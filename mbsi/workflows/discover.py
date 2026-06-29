"""Discovery intelligence — communication, TME, biomarkers, causal drivers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_discover_workflow(
    readiness: Optional[Dict[str, Any]] = None,
    seed: int = 42,
    substep: str = "full",
) -> RunRecord:
    try:
        from mbsi.discovery.engine import run_discovery_engine

        out = run_discovery_engine(seed=seed, readiness=readiness)
        return RunRecord.success(
            module=WorkflowModule.DISCOVERY.value,
            inputs={"seed": seed, "substep": substep},
            outputs={
                "findings_count": len(out.get("findings", [])),
                "status": out.get("status"),
                "discovery_results": out,
            },
            warnings=out.get("warnings", []),
        )
    except Exception as exc:
        return RunRecord.failed(WorkflowModule.DISCOVERY.value, str(exc))
