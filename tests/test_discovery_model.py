"""Tests for discovery model entities and store."""

from mbsi.discovery_model import (
    Evidence,
    Finding,
    FindingStore,
    FindingType,
    confidence_level,
    create_evidence,
)
from mbsi.discovery_model.ontology import FINDING_TYPE_LABELS


def test_finding_to_dict_roundtrip():
    f = Finding.create(
        title="Immune exclusion at tumor edge",
        summary="CD8 exclusion detected",
        finding_type=FindingType.IMMUNE_EXCLUSION.value,
        module="tme",
        confidence_score=72.0,
        confidence_level="Moderate",
    )
    restored = Finding.from_dict(f.to_dict())
    assert restored.title == f.title
    assert restored.finding_type == FindingType.IMMUNE_EXCLUSION.value


def test_evidence_to_dict_roundtrip():
    ev = create_evidence("benchmark", "metric", "Pearson score", value=0.85)
    restored = Evidence.from_dict(ev.to_dict())
    assert restored.evidence_id == ev.evidence_id
    assert restored.value == 0.85


def test_confidence_level_thresholds():
    assert confidence_level(80) == "High"
    assert confidence_level(60) == "Moderate"
    assert confidence_level(30) == "Exploratory"
    assert confidence_level(10) == "Hypothesis"


def test_finding_store_session():
    store = FindingStore()
    ev = create_evidence("tme", "niche", "Hypoxia niche", value=12)
    store.add_evidence(ev)
    f = Finding.create(
        title="Hypoxia",
        summary="Hypoxic niche",
        finding_type=FindingType.HYPOXIA_NICHE.value,
        module="tme",
        evidence_ids=[ev.evidence_id],
    )
    store.add(f)
    session = store.to_session_dict()
    restored = FindingStore.from_session_dict(session)
    assert len(restored.list_findings()) == 1
    assert restored.list_findings()[0].title == "Hypoxia"


def test_ontology_labels():
    assert FINDING_TYPE_LABELS[FindingType.LR_PATHWAY] == "Ligand-Receptor Pathway"
