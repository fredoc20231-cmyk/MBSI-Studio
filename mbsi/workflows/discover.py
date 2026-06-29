"""Discovery intelligence — communication, TME, biomarkers, causal drivers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_discover_workflow(
    adata: Any = None,
    readiness: Optional[Dict[str, Any]] = None,
    seed: int = 42,
    substep: str = "full",
    allow_demo: bool = False,
    analysis_results: Optional[Dict[str, Any]] = None,
) -> RunRecord:
    try:
        from mbsi.discovery.engine import run_discovery_engine

        out = run_discovery_engine(
            adata=adata,
            seed=seed,
            readiness=readiness,
            allow_demo=allow_demo,
            analysis_results=analysis_results,
        )
        if out.get("status") == "unavailable":
            return RunRecord.failed(
                WorkflowModule.DISCOVERY.value,
                out.get("warnings", ["Discovery unavailable — upload real data first"])[0],
            )
        return RunRecord.success(
            module=WorkflowModule.DISCOVERY.value,
            inputs={"seed": seed, "substep": substep, "allow_demo": allow_demo},
            outputs={
                "findings_count": len(out.get("findings", [])),
                "status": out.get("status"),
                "discovery_results": out,
                "is_demo": out.get("is_demo", False),
            },
            warnings=out.get("warnings", []),
        )
    except Exception as exc:
        return RunRecord.failed(WorkflowModule.DISCOVERY.value, str(exc))
