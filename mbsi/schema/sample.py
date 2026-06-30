"""Sample record schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SampleRecord:
    sample_id: str
    patient_id: str = ""
    condition: str = ""
    timepoint: str = ""
    replicate_id: str = ""
    platform: str = ""
    technology: str = ""
    file_name: str = ""
    tissue_region: str = ""
    notes: str = ""
    comparison_group: str = ""
    project_id: str = ""
    dataset_id: str = ""
    run_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "patient_id": self.patient_id,
            "condition": self.condition,
            "timepoint": self.timepoint,
            "replicate_id": self.replicate_id,
            "platform": self.platform,
            "technology": self.technology or self.platform,
            "file_name": self.file_name,
            "tissue_region": self.tissue_region,
            "notes": self.notes,
            "comparison_group": self.comparison_group,
            "project_id": self.project_id,
            "dataset_id": self.dataset_id,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SampleRecord":
        return cls(
            sample_id=str(data.get("sample_id", "")),
            patient_id=str(data.get("patient_id", "")),
            condition=str(data.get("condition", "")),
            timepoint=str(data.get("timepoint", "")),
            replicate_id=str(data.get("replicate_id", "")),
            platform=str(data.get("platform", "")),
            technology=str(data.get("technology", "") or data.get("platform", "")),
            file_name=str(data.get("file_name", "")),
            tissue_region=str(data.get("tissue_region", "")),
            notes=str(data.get("notes", "")),
            comparison_group=str(data.get("comparison_group", "")),
            project_id=str(data.get("project_id", "")),
            dataset_id=str(data.get("dataset_id", "")),
            run_id=str(data.get("run_id", "")),
        )

    @classmethod
    def from_rows(cls, rows: List[Dict[str, Any]]) -> List["SampleRecord"]:
        return [cls.from_dict(r) for r in rows if r.get("sample_id")]


SAMPLE_COLUMNS = [
    "sample_id",
    "patient_id",
    "condition",
    "timepoint",
    "replicate_id",
    "platform",
    "technology",
    "file_name",
    "tissue_region",
    "notes",
    "comparison_group",
]
