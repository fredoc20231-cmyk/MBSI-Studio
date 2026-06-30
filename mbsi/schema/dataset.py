"""Dataset readiness and file inventory schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from mbsi.schema.traceability import TraceabilityFields


@dataclass
class DatasetRecord:
    files_uploaded: List[str] = field(default_factory=list)
    modalities: List[str] = field(default_factory=list)
    readiness_scores: Dict[str, float] = field(default_factory=dict)
    spatial_coords_present: bool = False
    gene_names_present: bool = False
    technology_key: str = ""
    detection: Dict[str, Any] = field(default_factory=dict)
    adata_path: str = ""
    traceability: TraceabilityFields = field(default_factory=TraceabilityFields)

    @property
    def project_readiness(self) -> float:
        return float(self.readiness_scores.get("project", 0))

    @property
    def dataset_readiness(self) -> float:
        return float(self.readiness_scores.get("dataset", 0))

    @property
    def dataset_id(self) -> str:
        return self.traceability.dataset_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_uploaded": list(self.files_uploaded),
            "modalities": list(self.modalities),
            "readiness_scores": dict(self.readiness_scores),
            "spatial_coords_present": self.spatial_coords_present,
            "gene_names_present": self.gene_names_present,
            "technology_key": self.technology_key,
            "detection": dict(self.detection),
            "adata_path": self.adata_path,
            **self.traceability.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetRecord":
        trace = TraceabilityFields.from_dict(data)
        if not trace.dataset_id:
            trace.dataset_id = str(data.get("dataset_id", ""))
        if not trace.technology:
            trace.technology = str(data.get("technology_key", ""))
        return cls(
            files_uploaded=list(data.get("files_uploaded", [])),
            modalities=list(data.get("modalities", [])),
            readiness_scores=dict(data.get("readiness_scores", {})),
            spatial_coords_present=bool(data.get("spatial_coords_present", False)),
            gene_names_present=bool(data.get("gene_names_present", False)),
            technology_key=str(data.get("technology_key", "")),
            detection=dict(data.get("detection", {})),
            adata_path=str(data.get("adata_path", "")),
            traceability=trace,
        )

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
