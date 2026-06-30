"""Shared traceability fields for schema entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class TraceabilityFields:
    project_id: str = ""
    sample_id: str = ""
    condition: str = ""
    replicate_id: str = ""
    technology: str = ""
    dataset_id: str = ""
    run_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "sample_id": self.sample_id,
            "condition": self.condition,
            "replicate_id": self.replicate_id,
            "technology": self.technology,
            "dataset_id": self.dataset_id,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "TraceabilityFields":
        if not data:
            return cls()
        return cls(
            project_id=str(data.get("project_id", "")),
            sample_id=str(data.get("sample_id", "")),
            condition=str(data.get("condition", "")),
            replicate_id=str(data.get("replicate_id", "")),
            technology=str(data.get("technology", "")),
            dataset_id=str(data.get("dataset_id", "")),
            run_id=str(data.get("run_id", "")),
        )

    def merge_into(self, target: Dict[str, Any]) -> Dict[str, Any]:
        target.update(self.to_dict())
        return target
