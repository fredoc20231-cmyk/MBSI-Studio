"""Report metadata linking project, samples, findings, and files."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mbsi.schema.project import ProjectMetadata
from mbsi.schema.sample import SampleRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ReportMetadata:
    project: ProjectMetadata = field(default_factory=ProjectMetadata)
    samples: List[SampleRecord] = field(default_factory=list)
    finding_ids: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_utc_now)
    report_type: str = "html"
    traceability: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project.to_dict(),
            "samples": [s.to_dict() for s in self.samples],
            "finding_ids": list(self.finding_ids),
            "evidence_ids": list(self.evidence_ids),
            "output_files": list(self.output_files),
            "generated_at": self.generated_at,
            "report_type": self.report_type,
            "traceability": dict(self.traceability),
        }

    @classmethod
    def from_session_snapshot(cls, snapshot: Dict[str, Any]) -> "ReportMetadata":
        project_raw = snapshot.get("project_metadata") or {}
        samples_raw = snapshot.get("sample_metadata") or []
        findings = snapshot.get("findings") or []
        evidence = snapshot.get("evidence") or []
        return cls(
            project=ProjectMetadata.from_session(project_raw),
            samples=SampleRecord.from_rows(samples_raw) if isinstance(samples_raw, list) else [],
            finding_ids=[f.get("finding_id", "") for f in findings if isinstance(f, dict)],
            evidence_ids=[e.get("evidence_id", "") for e in evidence if isinstance(e, dict)],
            output_files=snapshot.get("output_files", []),
            traceability={
                "last_run": snapshot.get("last_run"),
                "dataset_readiness": snapshot.get("dataset_readiness"),
                "project_completeness": snapshot.get("project_completeness"),
            },
        )
