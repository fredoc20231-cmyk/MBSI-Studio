"""Workflow run record schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    module: str
    timestamp: str = field(default_factory=_utc_now)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    run_id: str = field(default_factory=lambda: str(uuid4()))
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "module": self.module,
            "timestamp": self.timestamp,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunRecord":
        return cls(
            run_id=data.get("run_id", str(uuid4())),
            module=data["module"],
            timestamp=data.get("timestamp", _utc_now()),
            inputs=dict(data.get("inputs", {})),
            outputs=dict(data.get("outputs", {})),
            status=data.get("status", "pending"),
            warnings=list(data.get("warnings", [])),
        )

    @classmethod
    def success(
        cls,
        module: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "RunRecord":
        return cls(
            module=module,
            inputs=inputs or {},
            outputs=outputs or {},
            status="success",
            warnings=warnings or [],
        )

    @classmethod
    def failed(cls, module: str, error: str, inputs: Optional[Dict[str, Any]] = None) -> "RunRecord":
        return cls(
            module=module,
            inputs=inputs or {},
            status="failed",
            warnings=[error],
        )
