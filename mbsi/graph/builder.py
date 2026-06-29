"""Discovery graph builder — Finding → Evidence → Outcome."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad
import pandas as pd

from mbsi.discovery_model.entities import Evidence, Finding
from mbsi.discovery_model.ontology import FINDING_TYPE_LABELS


NODE_TYPES = ("Bin", "Cell", "Region", "Neighborhood", "Niche", "Pathway", "Biomarker", "Finding", "Outcome")
EDGE_TYPES = ("contained_in", "adjacent_to", "transition_to", "participates_in", "associated_with", "enriched_in", "supported_by", "drives")


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


def populate_stereo_seq_spatial_graph(adata: ad.AnnData) -> Dict[str, Any]:
    """
    Populate Bin → Cell → Neighborhood → Niche graph from Stereo-seq AnnData obs/obsm.

    Returns nodes/edges fragment to merge into discovery graph.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    if "spatial" not in adata.obsm:
        return {"nodes": nodes, "edges": edges}

    scale = adata.obs.get("stereo_scale", "bin")
    default_scale = str(scale.iloc[0]) if hasattr(scale, "iloc") else str(scale)

    for i, obs_name in enumerate(adata.obs_names[: min(500, adata.n_obs)]):
        node_type = "Bin" if default_scale == "bin" else "Cell"
        if "cell_id" in adata.obs and pd.notna(adata.obs["cell_id"].iloc[i]):
            node_type = "Cell"
        nid = f"spatial:{obs_name}"
        nodes.append({"id": nid, "type": node_type, "label": str(obs_name)})
        if "region_id" in adata.obs:
            rid = adata.obs["region_id"].iloc[i]
            region_node = f"region:{rid}"
            if not any(n["id"] == region_node for n in nodes):
                nodes.append({"id": region_node, "type": "Region", "label": str(rid)})
            edges.append({"source": nid, "target": region_node, "type": "contained_in"})

    if "cluster" in adata.obs:
        for cl in adata.obs["cluster"].astype(str).unique()[:20]:
            niche_id = f"niche:{cl}"
            nodes.append({"id": niche_id, "type": "Niche", "label": f"Niche {cl}"})
            members = adata.obs_names[adata.obs["cluster"].astype(str) == cl][:50]
            for obs_name in members:
                edges.append({"source": f"spatial:{obs_name}", "target": niche_id, "type": "contained_in"})

    return {"nodes": nodes, "edges": edges}


def build_discovery_graph(
    findings: List[Finding],
    evidence_list: List[Evidence],
    adata: Optional[ad.AnnData] = None,
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

    stereo_fragment: Dict[str, Any] = {"nodes": [], "edges": []}
    if adata is not None and adata.uns.get("mbsi_platform") == "stereo_seq":
        stereo_fragment = populate_stereo_seq_spatial_graph(adata)
        nodes.extend(stereo_fragment["nodes"])
        edges.extend(stereo_fragment["edges"])
        for finding in findings:
            if finding.finding_type in ("biomarker", "niche", "lr_pathway"):
                biom_node = f"biomarker:{finding.finding_id}"
                nodes.append({
                    "id": biom_node,
                    "type": "Biomarker",
                    "label": finding.title,
                })
                niche_nodes = [n["id"] for n in stereo_fragment["nodes"] if n["type"] == "Niche"]
                if niche_nodes:
                    edges.append({
                        "source": niche_nodes[0],
                        "target": biom_node,
                        "type": "transition_to",
                    })

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "n_findings": len(findings),
            "n_evidence": len(evidence_list),
            "node_types": list(NODE_TYPES),
            "edge_types": list(EDGE_TYPES),
            "stereo_seq_spatial_nodes": len(stereo_fragment.get("nodes", [])),
        },
    }
