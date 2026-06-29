"""Evidence schema — re-export and extend discovery_model Evidence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.discovery_model.entities import Evidence
from mbsi.discovery_model.evidence import create_evidence, evidence_from_registry

__all__ = ["Evidence", "create_evidence", "evidence_from_registry", "evidence_with_sample_metadata"]


def evidence_with_sample_metadata(
    evidence: Evidence,
    sample_id: Optional[str] = None,
    platform: Optional[str] = None,
) -> Evidence:
    """Attach sample traceability into evidence metadata."""
    meta = dict(evidence.metadata)
    if sample_id:
        meta["sample_id"] = sample_id
    if platform:
        meta["platform"] = platform
    evidence.metadata = meta
    return evidence


def evidence_list_from_dicts(rows: List[Dict[str, Any]]) -> List[Evidence]:
    return [Evidence.from_dict(r) for r in rows]
