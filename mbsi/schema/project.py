"""Project-level metadata schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProjectMetadata:
    title: str = ""
    biological_question: str = ""
    disease_context: str = ""
    study_objective: str = ""
    organism: str = "Human"
    therapeutic_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "biological_question": self.biological_question,
            "disease_context": self.disease_context,
            "study_objective": self.study_objective,
            "organism": self.organism,
            "therapeutic_context": self.therapeutic_context,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ProjectMetadata":
        if not data:
            return cls()
        return cls(
            title=data.get("title") or data.get("project_title", ""),
            biological_question=data.get("biological_question", ""),
            disease_context=data.get("disease_context", ""),
            study_objective=data.get("study_objective", ""),
            organism=data.get("organism", "Human"),
            therapeutic_context=data.get("therapeutic_context", ""),
        )

    @classmethod
    def from_session(cls, session_meta: Optional[Dict[str, Any]]) -> "ProjectMetadata":
        """Map legacy session key `project_metadata` to schema object."""
        if not session_meta:
            return cls()
        return cls(
            title=session_meta.get("project_title") or session_meta.get("title", ""),
            biological_question=session_meta.get("biological_question", ""),
            disease_context=session_meta.get("disease_context", ""),
            study_objective=session_meta.get("study_objective", ""),
            organism=session_meta.get("organism", "Human"),
            therapeutic_context=session_meta.get("therapeutic_context", ""),
        )
