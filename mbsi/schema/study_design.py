"""Experimental study design schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StudyDesign:
    study_type: str = ""
    num_samples: int = 1
    has_replicates: str = "Not sure"
    replicate_type: str = ""
    comparison_groups: str = ""
    timepoints: List[str] = field(default_factory=list)
    treatment_arms: List[str] = field(default_factory=list)
    primary_comparison: str = ""
    secondary_comparisons: List[str] = field(default_factory=list)
    patient_ids: List[str] = field(default_factory=list)
    project_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "study_type": self.study_type,
            "num_samples": self.num_samples,
            "has_replicates": self.has_replicates,
            "replicate_type": self.replicate_type,
            "comparison_groups": self.comparison_groups,
            "timepoints": list(self.timepoints),
            "treatment_arms": list(self.treatment_arms),
            "primary_comparison": self.primary_comparison,
            "secondary_comparisons": list(self.secondary_comparisons),
            "patient_ids": list(self.patient_ids),
            "project_id": self.project_id,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "StudyDesign":
        if not data:
            return cls()
        timepoints = data.get("timepoints") or []
        if isinstance(timepoints, str):
            timepoints = [t.strip() for t in timepoints.split(",") if t.strip()]
        arms = data.get("treatment_arms") or []
        if isinstance(arms, str):
            arms = [a.strip() for a in arms.split(",") if a.strip()]
        secondary = data.get("secondary_comparisons") or []
        if isinstance(secondary, str):
            secondary = [s.strip() for s in secondary.split(",") if s.strip()]
        patients = data.get("patient_ids") or []
        if isinstance(patients, str):
            patients = [p.strip() for p in patients.split(",") if p.strip()]
        return cls(
            study_type=str(data.get("study_type", "")),
            num_samples=int(data.get("num_samples", 1)),
            has_replicates=str(data.get("has_replicates", "Not sure")),
            replicate_type=str(data.get("replicate_type", "")),
            comparison_groups=str(data.get("comparison_groups", "")),
            timepoints=list(timepoints),
            treatment_arms=list(arms),
            primary_comparison=str(data.get("primary_comparison", "")),
            secondary_comparisons=list(secondary),
            patient_ids=list(patients),
            project_id=str(data.get("project_id", "")),
        )

    @classmethod
    def from_session(
        cls,
        design: Optional[Dict[str, Any]] = None,
        project_id: str = "",
    ) -> "StudyDesign":
        obj = cls.from_dict(design)
        if project_id and not obj.project_id:
            obj.project_id = project_id
        return obj
