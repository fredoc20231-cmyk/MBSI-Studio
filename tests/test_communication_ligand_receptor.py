"""Tests for ligand-receptor scoring."""

from mbsi.communication import (
    score_ligand_receptor_pairs,
    pathway_rankings,
    make_communication_demo_adata,
    DEFAULT_PATHWAYS,
)


def test_score_ligand_receptor_pairs():
    adata = make_communication_demo_adata(n_spots=60, seed=0)
    df = score_ligand_receptor_pairs(adata)
    assert not df.empty
    assert "score" in df.columns
    assert "probability" in df.columns
    assert df["status"].eq("ok").any()


def test_pathway_rankings():
    adata = make_communication_demo_adata(n_spots=50, seed=1)
    rankings = pathway_rankings(adata)
    assert len(rankings) == len(DEFAULT_PATHWAYS)
    assert rankings.iloc[0]["score"] >= rankings.iloc[-1]["score"]


def test_missing_genes_handled():
    from mbsi.analysis.demo import make_synthetic_visium_adata

    adata = make_synthetic_visium_adata(n_spots=30, n_genes=20, seed=2)
    df = score_ligand_receptor_pairs(adata, pairs=[("FAKE_L", "FAKE_R")])
    assert df.iloc[0]["status"] == "missing_genes"
