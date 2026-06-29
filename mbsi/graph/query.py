"""Discovery graph queries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def get_related_findings(finding_id: str, graph: Dict[str, Any]) -> List[str]:
    """Return finding IDs sharing evidence or outcome paths."""
    related: set[str] = set()
    edges = graph.get("edges", [])
    nodes = {n["id"]: n for n in graph.get("nodes", [])}

    target = f"finding:{finding_id}" if not finding_id.startswith("finding:") else finding_id
    if target not in nodes:
        return []

    evidence_nodes = [e["source"] for e in edges if e["target"] == target and e["type"] == "supported_by"]
    for evid in evidence_nodes:
        for e in edges:
            if e["source"] == evid and e["target"] != target and e["target"].startswith("finding:"):
                related.add(e["target"].replace("finding:", ""))

    for e in edges:
        if e["source"] == target and e["type"] == "drives":
            outcome = e["target"]
            for e2 in edges:
                if e2["target"] == outcome and e2["source"].startswith("finding:"):
                    fid = e2["source"].replace("finding:", "")
                    if fid != finding_id.replace("finding:", ""):
                        related.add(fid)
    return sorted(related)


def get_path_to_outcome(finding_id: str, graph: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return path finding → evidence → outcome as list of steps."""
    target = f"finding:{finding_id}" if not finding_id.startswith("finding:") else finding_id
    path: List[Dict[str, str]] = [{"step": "finding", "id": target}]

    for e in graph.get("edges", []):
        if e["target"] == target and e["type"] == "supported_by":
            path.insert(0, {"step": "evidence", "id": e["source"]})

    for e in graph.get("edges", []):
        if e["source"] == target and e["type"] == "drives":
            path.append({"step": "outcome", "id": e["target"]})
            break
    return path
