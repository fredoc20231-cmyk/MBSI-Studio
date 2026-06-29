"""Study setup + technology-aware ingestion workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.schema.dataset import DatasetRecord
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.run import RunRecord
from mbsi.schema.sample import SampleRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule


def run_ingest_workflow(
    project: ProjectMetadata,
    samples: List[SampleRecord],
    files: Optional[List[str]] = None,
    adata: Any = None,
    ingestion: Optional[Dict[str, Any]] = None,
    technology_key: str = "",
    project_score: float = 0,
    dataset_score: float = 0,
) -> RunRecord:
    """Evaluate ingestion readiness and compatibility from schema objects."""
    detection = (ingestion or {}).get("detection") or detect_platform(files or [])
    tech_key = technology_key or detection.get("technology_key", "")
    tech = get_technology(tech_key)
    dataset = DatasetRecord.from_session(
        adata=adata,
        ingestion=ingestion,
        project_score=project_score,
        dataset_score=dataset_score,
        uploaded_files=files,
    )
    matrix = get_compatibility_matrix(adata, detection, technology_key=tech_key)
    warnings: List[str] = []
    if detection.get("partial_support"):
        warnings.append(f"{tech.label if tech else tech_key}: partial loader support")
    if detection.get("missing"):
        warnings.extend(detection["missing"])

    return RunRecord.success(
        module=WorkflowModule.STUDY_SETUP.value,
        inputs={
            "project": project.to_dict(),
            "samples": [s.to_dict() for s in samples],
            "technology_key": tech_key,
            "files": files or [],
        },
        outputs={
            "dataset": dataset.to_dict(),
            "detection": detection,
            "compatibility": matrix,
            "technology_spec": tech.to_dict() if tech else {},
        },
        warnings=warnings,
    )
