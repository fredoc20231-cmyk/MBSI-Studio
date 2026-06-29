"""Dataset readiness and file inventory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DatasetRecord:
    files_uploaded: List[str] = field(default_factory=list)
    modalities: List[str] = field(default_factory=list)
    readiness_scores: Dict[str, float] = field(default_factory=dict)
    spatial_coords_present: bool = False
    gene_names_present: bool = False
    technology_key: str = ""
    detection: Dict[str, Any] = field(default_factory=dict)

    @property
    def project_readiness(self) -> float:
        return float(self.readiness_scores.get("project", 0))

    @property
    def dataset_readiness(self) -> float:
        return float(self.readiness_scores.get("dataset", 0))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_uploaded": list(self.files_uploaded),
            "modalities": list(self.modalities),
            "readiness_scores": dict(self.readiness_scores),
            "spatial_coords_present": self.spatial_coords_present,
            "gene_names_present": self.gene_names_present,
            "technology_key": self.technology_key,
            "detection": dict(self.detection),
        }

    @classmethod
    def from_session(
        cls,
        adata: Any = None,
        ingestion: Optional[Dict[str, Any]] = None,
        project_score: float = 0,
        dataset_score: float = 0,
        uploaded_files: Optional[List[str]] = None,
    ) -> "DatasetRecord":
        detection = (ingestion or {}).get("detection", {})
        tech = detection.get("platform") or detection.get("technology_key", "")
        spatial = False
        genes = False
        if adata is not None:
            spatial = "spatial" in getattr(adata, "obsm", {})
            genes = getattr(adata, "n_vars", 0) >= 1
            tech = tech or getattr(adata, "uns", {}).get("mbsi_platform", "")
        return cls(
            files_uploaded=list(uploaded_files or []),
            modalities=(ingestion or {}).get("modalities", []),
            readiness_scores={"project": project_score, "dataset": dataset_score},
            spatial_coords_present=spatial,
            gene_names_present=genes,
            technology_key=str(tech),
            detection=dict(detection),
        )
