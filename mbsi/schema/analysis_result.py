"""Analysis result schema with full sample/run traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AnalysisResult:
    module: str = ""
    result_type: str = ""
    project_id: str = ""
    sample_id: str = ""
    condition: str = ""
    replicate_id: str = ""
    technology: str = ""
    dataset_id: str = "default"
    run_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "result_type": self.result_type,
            "project_id": self.project_id,
            "sample_id": self.sample_id,
            "condition": self.condition,
            "replicate_id": self.replicate_id,
            "technology": self.technology,
            "dataset_id": self.dataset_id,
            "run_id": self.run_id,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        return cls(
            module=str(data.get("module", "")),
            result_type=str(data.get("result_type", "")),
            project_id=str(data.get("project_id", "")),
            sample_id=str(data.get("sample_id", "")),
            condition=str(data.get("condition", "")),
            replicate_id=str(data.get("replicate_id", "")),
            technology=str(data.get("technology", "")),
            dataset_id=str(data.get("dataset_id", "default")),
            run_id=str(data.get("run_id", "")),
            payload=dict(data.get("payload", {})),
        )

    @classmethod
    def from_run(
        cls,
        module: str,
        result_type: str,
        run_id: str,
        payload: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "AnalysisResult":
        ctx = context or {}
        return cls(
            module=module,
            result_type=result_type,
            run_id=run_id,
            payload=payload or {},
            project_id=str(ctx.get("project_id", "")),
            sample_id=str(ctx.get("sample_id", "")),
            condition=str(ctx.get("condition", "")),
            replicate_id=str(ctx.get("replicate_id", "")),
            technology=str(ctx.get("technology", "")),
            dataset_id=str(ctx.get("dataset_id", "default")),
        )
