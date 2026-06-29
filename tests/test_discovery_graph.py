"""Tests for discovery graph builder and queries."""

from mbsi.discovery_model import Finding, create_evidence
from mbsi.graph import build_discovery_graph, export_graph_json, get_path_to_outcome, get_related_findings


def test_build_discovery_graph():
    ev = create_evidence("communication", "pathway", "CXCL12 pathway")
    f1 = Finding.create(
        title="Signaling",
        summary="Top pathway",
        finding_type="lr_pathway",
        module="communication",
        evidence_ids=[ev.evidence_id],
        confidence_score=65,
        confidence_level="Moderate",
    )
    f2 = Finding.create(
        title="Niche",
        summary="Immune niche",
        finding_type="immune_exclusion",
        module="tme",
        confidence_score=55,
        confidence_level="Moderate",
    )
    graph = build_discovery_graph([f1, f2], [ev])
    assert len(graph["nodes"]) >= 3
    assert len(graph["edges"]) >= 2
    assert graph["meta"]["n_findings"] == 2


def test_get_path_to_outcome():
    ev = create_evidence("tme", "niche", "Niche A")
    f = Finding.create(
        title="Niche finding",
        summary="Niche",
        finding_type="niche",
        module="tme",
        evidence_ids=[ev.evidence_id],
    )
    graph = build_discovery_graph([f], [ev])
    path = get_path_to_outcome(f.finding_id, graph)
    assert any(p["step"] == "finding" for p in path)
    assert any(p["step"] == "outcome" for p in path)


def test_export_graph_json(tmp_path):
    f = Finding.create(title="T", summary="S", finding_type="biomarker", module="tme")
    graph = build_discovery_graph([f], [])
    path = export_graph_json(graph, tmp_path / "graph.json")
    assert path.exists()
    assert "nodes" in path.read_text()
