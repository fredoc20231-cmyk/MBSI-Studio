"""WorkflowRun entity — traceable workflow execution record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from mbsi.schema.traceability import TraceabilityFields


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WorkflowRun:
    module: str
    timestamp: str = field(default_factory=_utc_now)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    warnings: List[str] = field(default_factory=list)
    traceability: TraceabilityFields = field(default_factory=TraceabilityFields)

    @property
    def run_id(self) -> str:
        return self.traceability.run_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "timestamp": self.timestamp,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status,
            "warnings": list(self.warnings),
            **self.traceability.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowRun":
        trace = TraceabilityFields.from_dict(data)
        if not trace.run_id:
            trace.run_id = str(data.get("run_id", uuid4()))
        return cls(
            module=str(data.get("module", "")),
            timestamp=str(data.get("timestamp", _utc_now())),
            inputs=dict(data.get("inputs", {})),
            outputs=dict(data.get("outputs", {})),
            status=str(data.get("status", "pending")),
            warnings=list(data.get("warnings", [])),
            traceability=trace,
        )

    @classmethod
    def success(
        cls,
        module: str,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        project_id: str = "",
        dataset_id: str = "",
        run_id: Optional[str] = None,
    ) -> "WorkflowRun":
        return cls(
            module=module,
            inputs=inputs or {},
            outputs=outputs or {},
            status="success",
            warnings=warnings or [],
            traceability=TraceabilityFields(
                project_id=project_id,
                dataset_id=dataset_id,
                run_id=run_id or str(uuid4()),
            ),
        )
