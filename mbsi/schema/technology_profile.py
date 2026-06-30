"""Technology profile entity with traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from mbsi.schema.technology import TechnologySpec, get_technology
from mbsi.schema.traceability import TraceabilityFields


@dataclass
class TechnologyProfile:
    key: str = ""
    label: str = ""
    spec: Dict[str, Any] = field(default_factory=dict)
    traceability: TraceabilityFields = field(default_factory=TraceabilityFields)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "spec": dict(self.spec),
            **self.traceability.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechnologyProfile":
        trace = TraceabilityFields.from_dict(data)
        spec = dict(data.get("spec", {}))
        key = str(data.get("key", spec.get("key", "")))
        label = str(data.get("label", spec.get("label", "")))
        return cls(key=key, label=label, spec=spec, traceability=trace)

    @classmethod
    def from_technology(
        cls,
        technology_key: str,
        *,
        project_id: str = "",
        sample_id: str = "",
        dataset_id: str = "",
    ) -> "TechnologyProfile":
        spec = get_technology(technology_key)
        spec_dict = spec.to_dict() if spec else {}
        return cls(
            key=technology_key,
            label=spec_dict.get("label", technology_key),
            spec=spec_dict,
            traceability=TraceabilityFields(
                project_id=project_id,
                sample_id=sample_id,
                technology=technology_key,
                dataset_id=dataset_id,
            ),
        )
