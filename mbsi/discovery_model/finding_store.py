"""Session-compatible finding store with optional persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mbsi.discovery_model.entities import Evidence, Finding


class FindingStore:
    """In-memory finding/evidence store compatible with session_state dicts."""

    def __init__(self, persist_path: Optional[Path] = None) -> None:
        self._findings: Dict[str, Finding] = {}
        self._evidence: Dict[str, Evidence] = {}
        self.persist_path = Path(persist_path) if persist_path else None

    @classmethod
    def from_session_dict(cls, session_dict: Optional[Dict[str, Any]] = None) -> "FindingStore":
        store = cls()
        if not session_dict:
            return store
        for ev in session_dict.get("evidence", []):
            e = Evidence.from_dict(ev) if isinstance(ev, dict) else ev
            store._evidence[e.evidence_id] = e
        for f in session_dict.get("findings", []):
            finding = Finding.from_dict(f) if isinstance(f, dict) else f
            store._findings[finding.finding_id] = finding
        return store

    def add_evidence(self, evidence: Evidence) -> Evidence:
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def add(self, finding: Finding) -> Finding:
        self._findings[finding.finding_id] = finding
        return finding

    def get(self, finding_id: str) -> Optional[Finding]:
        return self._findings.get(finding_id)

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        return self._evidence.get(evidence_id)

    def list_findings(self) -> List[Finding]:
        return sorted(self._findings.values(), key=lambda f: (-f.confidence_score, f.created_at))

    def list_evidence(self) -> List[Evidence]:
        return list(self._evidence.values())

    def to_session_dict(self) -> Dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.list_findings()],
            "evidence": [e.to_dict() for e in self.list_evidence()],
        }

    def persist(self, path: Optional[Path] = None) -> Path:
        target = Path(path or self.persist_path or "data/outputs/findings.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_session_dict(), indent=2, default=str))
        return target

    @classmethod
    def load(cls, path: Path) -> "FindingStore":
        data = json.loads(Path(path).read_text())
        return cls.from_session_dict(data)
