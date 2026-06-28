"""Tests for TME Intelligence upgrades."""

from pathlib import Path

from mbsi.tme import (
    run_tme_analysis,
    make_tme_demo_adata,
    TME_MARKER_SETS,
    score_marker_programs,
    program_summary,
    generate_tme_report,
)


def test_tme_marker_sets():
    assert "immune_exclusion" in TME_MARKER_SETS
    assert "CD8A" in TME_MARKER_SETS["immune_exclusion"]["immune"]
    assert "VEGFA" in TME_MARKER_SETS["angiogenesis"]["angiogenesis"]


def test_score_marker_programs():
    adata = make_tme_demo_adata(n_spots=80, seed=0)
    df = score_marker_programs(adata)
    assert not df.empty
    assert set(df["program"]).issubset(set(TME_MARKER_SETS.keys()))


def test_program_summary():
    adata = make_tme_demo_adata(n_spots=80, seed=1)
    scores = score_marker_programs(adata)
    summary = program_summary(scores)
    assert not summary.empty
    assert "mean_score" in summary.columns


def test_run_tme_includes_programs():
    results = run_tme_analysis(make_tme_demo_adata(n_spots=90, seed=2))
    assert "program_scores" in results
    assert "program_summary" in results
    assert not results["program_summary"].empty


def test_tme_niche_modules():
    results = run_tme_analysis(make_tme_demo_adata(n_spots=100, seed=3))
    for key in ("immune_exclusion", "tls_like", "caf_barriers", "hypoxic", "angiogenic", "invasive_fronts"):
        niche = results["niches"][key]
        assert "score" in niche
        assert "spatial_vector" in niche
        assert "table" in niche
        assert hasattr(niche["table"], "empty")
        assert "hypothesis" in niche


def test_generate_tme_report(tmp_path: Path):
    results = run_tme_analysis(make_tme_demo_adata(n_spots=60, seed=4))
    path = generate_tme_report(results, tmp_path)
    assert path.exists()
    assert "research use only" in path.read_text()
