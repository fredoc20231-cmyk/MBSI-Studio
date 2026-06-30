"""Project-level metadata schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import uuid4

from mbsi.schema.traceability import TraceabilityFields


@dataclass
class ProjectMetadata:
    title: str = ""
    biological_question: str = ""
    disease_context: str = ""
    study_objective: str = ""
    organism: str = "Human"
    therapeutic_context: str = ""
    traceability: TraceabilityFields = field(default_factory=TraceabilityFields)

    @property
    def project_id(self) -> str:
        return self.traceability.project_id

    @project_id.setter
    def project_id(self, value: str) -> None:
        self.traceability.project_id = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "biological_question": self.biological_question,
            "disease_context": self.disease_context,
            "study_objective": self.study_objective,
            "organism": self.organism,
            "therapeutic_context": self.therapeutic_context,
            **self.traceability.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ProjectMetadata":
        if not data:
            return cls()
        trace = TraceabilityFields.from_dict(data)
        if not trace.project_id:
            trace.project_id = str(data.get("project_id") or data.get("id") or uuid4())
        return cls(
            title=data.get("title") or data.get("project_title", ""),
            biological_question=data.get("biological_question", ""),
            disease_context=data.get("disease_context", ""),
            study_objective=data.get("study_objective", ""),
            organism=data.get("organism", "Human"),
            therapeutic_context=data.get("therapeutic_context", ""),
            traceability=trace,
        )

    @classmethod
    def from_session(cls, session_meta: Optional[Dict[str, Any]]) -> "ProjectMetadata":
        """Map legacy session key `project_metadata` to schema object."""
        obj = cls.from_dict(session_meta)
        if session_meta and not obj.traceability.project_id:
            obj.traceability.project_id = str(
                session_meta.get("project_id")
                or session_meta.get("project_title")
                or session_meta.get("title")
                or ""
            )
        return obj
