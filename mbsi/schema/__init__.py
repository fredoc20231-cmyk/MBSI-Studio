"""MBSI schema spine — project, sample, dataset, technology, workflow, run, findings."""

from mbsi.schema.analysis_result import AnalysisResult
from mbsi.schema.confidence import Confidence
from mbsi.schema.dataset import DatasetRecord
from mbsi.schema.evidence import Evidence, create_evidence, evidence_from_registry
from mbsi.schema.finding import Finding, finding_with_sample_context
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.report import ReportMetadata
from mbsi.schema.run import RunRecord
from mbsi.schema.sample import SAMPLE_COLUMNS, SampleRecord
from mbsi.schema.serialize import dumps, to_json_serializable
from mbsi.schema.study_design import StudyDesign
from mbsi.schema.technology import (
    TECHNOLOGIES,
    TECHNOLOGY_CATALOG,
    TECHNOLOGY_LABELS,
    UI_TECHNOLOGY_OPTIONS,
    TechnologySpec,
    get_technology,
    list_technologies,
    technology_from_label,
)
from mbsi.schema.technology_profile import TechnologyProfile
from mbsi.schema.traceability import TraceabilityFields
from mbsi.schema.workflow import (
    LEGACY_MODULE_MAP,
    WORKFLOW_MODULE_LABELS,
    WORKFLOW_SUBSTEPS,
    WorkflowModule,
    resolve_module_key,
)
from mbsi.schema.workflow_run import WorkflowRun

# Aliases for API / Builder.io contracts
Project = ProjectMetadata
Sample = SampleRecord
Dataset = DatasetRecord
Report = ReportMetadata

__all__ = [
    "AnalysisResult",
    "Confidence",
    "Dataset",
    "DatasetRecord",
    "Evidence",
    "Finding",
    "Project",
    "ProjectMetadata",
    "Report",
    "ReportMetadata",
    "RunRecord",
    "Sample",
    "SampleRecord",
    "StudyDesign",
    "TechnologyProfile",
    "TechnologySpec",
    "TraceabilityFields",
    "WorkflowRun",
    "SAMPLE_COLUMNS",
    "TECHNOLOGIES",
    "TECHNOLOGY_CATALOG",
    "TECHNOLOGY_LABELS",
    "UI_TECHNOLOGY_OPTIONS",
    "WorkflowModule",
    "WORKFLOW_MODULE_LABELS",
    "WORKFLOW_SUBSTEPS",
    "LEGACY_MODULE_MAP",
    "create_evidence",
    "dumps",
    "evidence_from_registry",
    "finding_with_sample_context",
    "get_technology",
    "list_technologies",
    "technology_from_label",
    "resolve_module_key",
    "to_json_serializable",
]
