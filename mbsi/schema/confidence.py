"""Confidence schema entity — scored finding confidence with traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from mbsi.discovery_model.confidence import confidence_level


@dataclass
class Confidence:
    finding_id: str = ""
    score: float = 0.0
    level: str = "Hypothesis"
    project_id: str = ""
    sample_id: str = ""
    condition: str = ""
    replicate_id: str = ""
    technology: str = ""
    dataset_id: str = "default"
    run_id: str = ""
    components: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "score": self.score,
            "level": self.level,
            "project_id": self.project_id,
            "sample_id": self.sample_id,
            "condition": self.condition,
            "replicate_id": self.replicate_id,
            "technology": self.technology,
            "dataset_id": self.dataset_id,
            "run_id": self.run_id,
            "components": dict(self.components),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Confidence":
        return cls(
            finding_id=str(data.get("finding_id", "")),
            score=float(data.get("score", 0)),
            level=str(data.get("level", "Hypothesis")),
            project_id=str(data.get("project_id", "")),
            sample_id=str(data.get("sample_id", "")),
            condition=str(data.get("condition", "")),
            replicate_id=str(data.get("replicate_id", "")),
            technology=str(data.get("technology", "")),
            dataset_id=str(data.get("dataset_id", "default")),
            run_id=str(data.get("run_id", "")),
            components=dict(data.get("components", {})),
        )

    @classmethod
    def from_finding(
        cls,
        finding: Any,
        run_id: str = "",
        project_id: str = "",
        dataset_id: str = "default",
        technology: str = "",
    ) -> "Confidence":
        score = float(getattr(finding, "confidence_score", 0) or 0)
        return cls(
            finding_id=str(getattr(finding, "finding_id", "")),
            score=score,
            level=str(getattr(finding, "confidence_level", "") or confidence_level(score)),
            project_id=project_id,
            sample_id=str(getattr(finding, "sample_id", "") or ""),
            condition=str(getattr(finding, "condition", "") or ""),
            replicate_id=str(getattr(finding, "replicate_id", "") or ""),
            technology=technology or str(getattr(finding, "platform", "") or ""),
            dataset_id=dataset_id,
            run_id=run_id or str(getattr(finding, "run_id", "") or ""),
        )
