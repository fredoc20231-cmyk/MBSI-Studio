"""Core Finding and Evidence entities for Discovery OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    evidence_id: str
    source_module: str
    evidence_type: str
    title: str
    description: str = ""
    ref_id: Optional[str] = None
    value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_module": self.source_module,
            "evidence_type": self.evidence_type,
            "title": self.title,
            "description": self.description,
            "ref_id": self.ref_id,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        return cls(
            evidence_id=data["evidence_id"],
            source_module=data["source_module"],
            evidence_type=data["evidence_type"],
            title=data["title"],
            description=data.get("description", ""),
            ref_id=data.get("ref_id"),
            value=data.get("value"),
            metadata=dict(data.get("metadata", {})),
            created_at=data.get("created_at", _utc_now()),
        )


@dataclass
class Finding:
    finding_id: str
    title: str
    summary: str
    finding_type: str
    module: str
    confidence_score: float = 0.0
    confidence_level: str = "Hypothesis"
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sample_id: Optional[str] = None
    condition: Optional[str] = None
    replicate_id: Optional[str] = None
    platform: Optional[str] = None
    technology: Optional[str] = None
    comparison_group: Optional[str] = None
    project_id: Optional[str] = None
    dataset_id: Optional[str] = None
    run_id: Optional[str] = None
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "summary": self.summary,
            "finding_type": self.finding_type,
            "module": self.module,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "evidence_ids": list(self.evidence_ids),
            "metadata": self.metadata,
            "sample_id": self.sample_id,
            "condition": self.condition,
            "replicate_id": self.replicate_id,
            "platform": self.platform,
            "technology": self.technology,
            "comparison_group": self.comparison_group,
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Finding":
        return cls(
            finding_id=data["finding_id"],
            title=data["title"],
            summary=data["summary"],
            finding_type=data["finding_type"],
            module=data["module"],
            confidence_score=float(data.get("confidence_score", 0)),
            confidence_level=data.get("confidence_level", "Hypothesis"),
            evidence_ids=list(data.get("evidence_ids", [])),
            metadata=dict(data.get("metadata", {})),
            sample_id=data.get("sample_id"),
            condition=data.get("condition"),
            replicate_id=data.get("replicate_id"),
            platform=data.get("platform"),
            technology=data.get("technology"),
            comparison_group=data.get("comparison_group"),
            project_id=data.get("project_id"),
            dataset_id=data.get("dataset_id"),
            run_id=data.get("run_id"),
            created_at=data.get("created_at", _utc_now()),
        )

    @classmethod
    def create(
        cls,
        title: str,
        summary: str,
        finding_type: str,
        module: str,
        **kwargs: Any,
    ) -> "Finding":
        return cls(
            finding_id=kwargs.pop("finding_id", str(uuid4())),
            title=title,
            summary=summary,
            finding_type=finding_type,
            module=module,
            **kwargs,
        )
