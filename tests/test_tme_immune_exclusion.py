"""Tests for immune exclusion detection."""

from mbsi.tme import detect_immune_exclusion, make_tme_demo_adata


def test_detect_immune_exclusion():
    adata = make_tme_demo_adata(n_spots=80, seed=0)
    result = detect_immune_exclusion(adata)
    assert "score" in result
    assert len(result["score"]) == adata.n_obs
    assert result["label"] == "Immune Exclusion"
    assert result["hypothesis"] == "computational_hypothesis"


def test_immune_exclusion_detects_niches():
    adata = make_tme_demo_adata(n_spots=100, seed=1)
    result = detect_immune_exclusion(adata)
    assert result["n_niches"] >= 0
    assert result["score"].max() <= 1.0 + 1e-6
