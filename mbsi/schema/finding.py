"""Finding schema — bridge to discovery_model with sample context helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.discovery_model.entities import Finding
from mbsi.schema.sample import SampleRecord

__all__ = ["Finding", "finding_with_sample_context", "findings_from_dicts"]


def finding_with_sample_context(
    finding: Finding,
    sample: Optional[SampleRecord] = None,
    comparison_group: Optional[str] = None,
) -> Finding:
    """Attach sample context to a Finding without mutating unrelated fields."""
    if sample is None:
        return finding
    if sample.sample_id:
        finding.sample_id = sample.sample_id
    if sample.condition:
        finding.condition = sample.condition
    if sample.replicate_id:
        finding.replicate_id = sample.replicate_id
    if sample.platform:
        finding.platform = sample.platform
    if comparison_group or sample.comparison_group:
        finding.comparison_group = comparison_group or sample.comparison_group
    return finding


def findings_from_dicts(rows: List[Dict[str, Any]]) -> List[Finding]:
    return [Finding.from_dict(r) for r in rows]
