"""Tests for copilot module."""

def test_copilot_query():
    from mbsi.copilot import answer_tissue_query
    state = {"boundaries": {"mean_boundary_score": 0.5}, "leakage_score": 0.1}
    ans = answer_tissue_query("Show tumor-stroma boundary regions.", state)
    assert "boundary" in ans.lower()


def test_query_templates():
    from mbsi.copilot import QUERY_TEMPLATES
    assert len(QUERY_TEMPLATES) >= 5
