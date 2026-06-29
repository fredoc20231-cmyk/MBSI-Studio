"""Discovery findings from segmentation outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from mbsi.confidence.engine import score_finding
from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.evidence import create_evidence
from mbsi.discovery_model.finding_store import FindingStore
from mbsi.discovery_model.ontology import FindingType
from mbsi.schema.finding import finding_with_sample_context


def _qc_gate(segmentation_qc: Optional[Dict[str, Any]]) -> bool:
    if not segmentation_qc:
        return False
    return bool(segmentation_qc.get("qc_pass") or segmentation_qc.get("metrics", {}).get("qc_pass"))


def build_segmentation_findings(
    adata: Any,
    boundary_result: Optional[Dict[str, Any]] = None,
    segmentation_qc: Optional[Dict[str, Any]] = None,
    readiness: Optional[Dict[str, Any]] = None,
) -> Tuple[FindingStore, List[Dict[str, Any]]]:
    """Create CAF barrier and immune exclusion findings from segmentation."""
    store = FindingStore()
    if not _qc_gate(segmentation_qc):
        return store, []

    if adata is None or "compartment" not in getattr(adata, "obs", {}):
        return store, []

    compartments = adata.obs["compartment"].astype(str).values
    n_tumor = int((compartments == "tumor").sum())
    n_immune = int((compartments == "immune").sum())
    n_stroma = int((compartments == "stroma").sum())

    boundary = boundary_result or {}
    boundary_scores = boundary.get("boundary_score")
    mean_boundary = float(boundary_scores.mean()) if boundary_scores is not None and len(boundary_scores) else 0.0

    if n_stroma > 0 and mean_boundary > 0.15:
        ev = create_evidence(
            "segmentation",
            "boundary",
            "Tumor-stroma interface",
            description=f"Mean boundary score {mean_boundary:.3f}",
            value=mean_boundary,
        )
        store.add_evidence(ev)
        finding = Finding.create(
            title="CAF barrier at tumor boundary",
            summary="Segmentation-derived tumor-stroma interface suggests stromal barrier at invasion front.",
            finding_type=FindingType.CAF_BARRIER.value,
            module="segment_register",
            evidence_ids=[ev.evidence_id],
            metadata={"mean_boundary_score": mean_boundary, "n_stroma": n_stroma},
        )
        score_finding(finding, [ev], {}, readiness)
        store.add(finding)

    tumor_frac = n_tumor / max(len(compartments), 1)
    immune_frac = n_immune / max(len(compartments), 1)
    if tumor_frac > 0.2 and immune_frac < 0.05 and n_immune > 0:
        ev = create_evidence(
            "segmentation",
            "compartment",
            "Immune exclusion zone",
            description=f"Immune fraction {immune_frac:.3f} near tumor regions",
            value=immune_frac,
        )
        store.add_evidence(ev)
        finding = Finding.create(
            title="Immune exclusion zone",
            summary="Low immune compartment fraction adjacent to tumor suggests spatial immune exclusion.",
            finding_type=FindingType.IMMUNE_EXCLUSION.value,
            module="segment_register",
            evidence_ids=[ev.evidence_id],
            metadata={"immune_fraction": immune_frac, "tumor_fraction": tumor_frac},
        )
        score_finding(finding, [ev], {}, readiness)
        store.add(finding)

    findings = [f.to_dict() for f in store.list_findings()]
    return store, findings
