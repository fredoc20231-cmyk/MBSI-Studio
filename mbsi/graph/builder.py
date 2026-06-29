"""Discovery graph builder — Finding → Evidence → Outcome."""

from __future__ import annotations

from typing import Any, Dict, List

from mbsi.discovery_model.entities import Evidence, Finding
from mbsi.discovery_model.ontology import FINDING_TYPE_LABELS


NODE_TYPES = ("Cell", "Neighborhood", "Niche", "Pathway", "Biomarker", "Finding", "Outcome")
EDGE_TYPES = ("participates_in", "associated_with", "enriched_in", "supported_by", "drives")


def _node_type_for_finding(finding_type: str) -> str:
    mapping = {
        "lr_pathway": "Pathway",
        "pathway": "Pathway",
        "biomarker": "Biomarker",
        "niche": "Niche",
        "hypoxia_niche": "Niche",
        "immune_exclusion": "Niche",
        "caf_barrier": "Neighborhood",
        "causal_driver": "Outcome",
        "benchmark": "Outcome",
        "reconstruction": "Outcome",
    }
    return mapping.get(finding_type, "Finding")


def build_discovery_graph(
    findings: List[Finding],
    evidence_list: List[Evidence],
) -> Dict[str, Any]:
    """Build nodes/edges dict for visualization and AI grounding."""
    evidence_by_id = {e.evidence_id: e for e in evidence_list}
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    outcome_id = "outcome:discovery"
    nodes.append({
        "id": outcome_id,
        "type": "Outcome",
        "label": "Discovery Outcome",
    })

    for finding in findings:
        fid = f"finding:{finding.finding_id}"
        nodes.append({
            "id": fid,
            "type": _node_type_for_finding(finding.finding_type),
            "label": finding.title,
            "finding_type": finding.finding_type,
            "confidence_score": finding.confidence_score,
            "confidence_level": finding.confidence_level,
        })
        edges.append({
            "source": fid,
            "target": outcome_id,
            "type": "drives",
            "weight": finding.confidence_score / 100.0,
        })

        for eid in finding.evidence_ids:
            ev = evidence_by_id.get(eid)
            if ev is None:
                continue
            evid_node = f"evidence:{eid}"
            nodes.append({
                "id": evid_node,
                "type": "Biomarker" if ev.evidence_type == "metric" else "Pathway",
                "label": ev.title,
                "evidence_type": ev.evidence_type,
            })
            edges.append({
                "source": evid_node,
                "target": fid,
                "type": "supported_by",
            })
            if ev.evidence_type in ("pathway", "niche"):
                edges.append({
                    "source": evid_node,
                    "target": fid,
                    "type": "enriched_in",
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "n_findings": len(findings),
            "n_evidence": len(evidence_list),
            "node_types": list(NODE_TYPES),
            "edge_types": list(EDGE_TYPES),
        },
    }
