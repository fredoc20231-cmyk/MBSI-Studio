"""Tests for validation recommendations."""

from mbsi.discovery_model import Finding
from mbsi.validation.recommendations import recommend_validations


def test_recommend_validations_lr_pathway():
    f = Finding.create(
        title="CXCL12 signaling",
        summary="Top LR pathway",
        finding_type="lr_pathway",
        module="communication",
        confidence_level="Moderate",
    )
    recs = recommend_validations([f])
    assert len(recs) == 1
    assert "RT-qPCR" in recs[0]["recommendations"][0] or "IF" in " ".join(recs[0]["recommendations"])


def test_recommend_validations_immune_exclusion():
    f = Finding.create(
        title="Immune exclusion",
        summary="CD8 excluded",
        finding_type="immune_exclusion",
        module="tme",
    )
    recs = recommend_validations([f])
    assert any("IF" in r or "Spatial" in r for r in recs[0]["recommendations"])
