"""Evidence creation linked to report registry outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from mbsi.discovery_model.entities import Evidence
from mbsi.reports.registry import get_registered_outputs


def create_evidence(
    source_module: str,
    evidence_type: str,
    title: str,
    description: str = "",
    ref_id: Optional[str] = None,
    value: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Evidence:
    """Create an Evidence record, optionally linking to registry ref_id."""
    return Evidence(
        evidence_id=str(uuid4()),
        source_module=source_module,
        evidence_type=evidence_type,
        title=title,
        description=description,
        ref_id=ref_id,
        value=value,
        metadata=metadata or {},
    )


def evidence_from_registry(module: str, limit: int = 5) -> List[Evidence]:
    """Build evidence objects from registered figures/tables for a module."""
    reg = get_registered_outputs()
    out: List[Evidence] = []
    for fig in reg.get("figures", []):
        if fig.get("module") != module:
            continue
        out.append(create_evidence(
            source_module=module,
            evidence_type="figure",
            title=fig.get("title", "Figure"),
            ref_id=str(fig.get("id")),
            metadata={"section": fig.get("section")},
        ))
    for tbl in reg.get("tables", []):
        if tbl.get("module") != module:
            continue
        out.append(create_evidence(
            source_module=module,
            evidence_type="table",
            title=tbl.get("title", "Table"),
            ref_id=str(tbl.get("id")),
            value={"rows": tbl.get("rows"), "columns": tbl.get("columns")},
        ))
    return out[:limit]
