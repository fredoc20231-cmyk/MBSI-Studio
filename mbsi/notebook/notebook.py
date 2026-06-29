"""Notebook integration — wraps report registry without duplication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mbsi.discovery_model.entities import Evidence, Finding
from mbsi.reports.registry import get_notebook_entries, register_finding


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class NotebookEntry:
    run_id: str
    timestamp: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    figures: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "findings": self.findings,
            "evidence": self.evidence,
            "figures": self.figures,
            "tables": self.tables,
            "summary": self.summary,
        }


def append_run(
    findings: List[Finding],
    evidence: List[Evidence],
    figures: Optional[List[Dict[str, Any]]] = None,
    tables: Optional[List[Dict[str, Any]]] = None,
    run_id: Optional[str] = None,
    summary: str = "",
) -> NotebookEntry:
    """
    Append a discovery run to the notebook via registry bridge.

    Registers top findings in mbsi.reports.registry and returns NotebookEntry.
    """
    run_id = run_id or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    entry = NotebookEntry(
        run_id=run_id,
        timestamp=_utc_now(),
        findings=[f.to_dict() for f in findings],
        evidence=[e.to_dict() for e in evidence],
        figures=figures or [],
        tables=tables or [],
        summary=summary,
    )
    for f in findings[:5]:
        register_finding(
            text=f.summary,
            section="discovery",
            module=f.module,
            title=f.title,
        )
    return entry


def get_notebook_runs() -> List[Dict[str, Any]]:
    """Return registry notebook entries (delegates to reports.registry)."""
    return get_notebook_entries()
