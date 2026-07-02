"""Pydantic request/response contracts for Builder.io-facing API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    ok: bool = True
    message: str = ""


class ProjectCreateRequest(BaseModel):
    title: str = ""
    biological_question: str = ""
    disease_context: str = ""
    study_objective: str = ""
    organism: str = "Human"
    therapeutic_context: str = ""


class ProjectCreateResponse(BaseModel):
    project_id: str
    project: Dict[str, Any]


class ProjectUpdateRequest(BaseModel):
    project_id: str
    title: Optional[str] = None
    biological_question: Optional[str] = None
    disease_context: Optional[str] = None
    study_objective: Optional[str] = None
    organism: Optional[str] = None
    therapeutic_context: Optional[str] = None


class ProjectUpdateResponse(BaseModel):
    project_id: str
    project: Dict[str, Any]


class DatasetUploadRequest(BaseModel):
    project_id: str = ""
    technology_hint: Optional[str] = Field(
        default=None,
        description="Milestone 1: visium | xenium | generic_h5ad (aliases: csv_matrix, h5ad)",
    )
    sample_id: str = ""


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    adata_path: str
    platform: str
    technology_profile: Dict[str, Any]
    readiness: Dict[str, Any]
    compatibility: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class DatasetInspectRequest(BaseModel):
    dataset_id: str
    source_path: Optional[str] = None


class DatasetInspectResponse(BaseModel):
    dataset_id: str
    platform: str
    technology_profile: Dict[str, Any]
    readiness: Dict[str, Any]
    compatibility: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DatasetReadinessResponse(BaseModel):
    dataset_id: str
    readiness: Dict[str, Any]
    compatibility: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)


class TechnologyListResponse(BaseModel):
    milestone_1_platforms: List[str] = Field(default_factory=list)
    technologies: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowRunRequest(BaseModel):
    project_id: str = ""
    dataset_id: str = "default"
    module: str = "discovery"
    params: Dict[str, Any] = Field(default_factory=dict)
    allow_demo: bool = False


class WorkflowRunResponse(BaseModel):
    run_id: str
    status: str
    module: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class WorkflowStatusResponse(BaseModel):
    run_id: str
    status: str
    module: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ResultsListResponse(BaseModel):
    dataset_id: str
    results: List[Dict[str, Any]] = Field(default_factory=list)


class FindingsListResponse(BaseModel):
    project_id: str = ""
    dataset_id: str = ""
    run_id: str = ""
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class EvidenceListResponse(BaseModel):
    project_id: str = ""
    dataset_id: str = ""
    run_id: str = ""
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class ReportGenerateRequest(BaseModel):
    project_id: str = ""
    dataset_id: str = ""
    run_id: str = ""
    report_type: str = "html"


class ReportGenerateResponse(BaseModel):
    report_id: str
    report: Dict[str, Any]
    output_files: List[str] = Field(default_factory=list)
