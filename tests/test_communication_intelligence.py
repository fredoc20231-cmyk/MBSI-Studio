"""Tests for Communication Intelligence Engine upgrades."""

from pathlib import Path

from mbsi.communication import (
    load_builtin_ligand_receptor_pairs,
    score_ligand_receptor_pairs,
    run_communication_analysis,
    compute_diffusion_weighted_signaling,
    build_sender_receiver_network,
    compute_niche_signaling_maps,
    generate_communication_report,
    make_communication_demo_adata,
    DEFAULT_PATHWAYS,
)


def test_load_builtin_ligand_receptor_pairs():
    df = load_builtin_ligand_receptor_pairs()
    assert len(df) == len(DEFAULT_PATHWAYS)
    assert "CXCL12" in df["ligand"].values
    assert "CXCR4" in df["receptor"].values
    assert "category" in df.columns


def test_score_ligand_receptor_full_schema():
    adata = make_communication_demo_adata(n_spots=60, seed=0)
    df = score_ligand_receptor_pairs(adata)
    assert not df.empty
    for col in ("ligand", "receptor", "pathway", "score", "probability", "status"):
        assert col in df.columns
    ok = df[df["status"] == "ok"]
    assert not ok.empty
    assert "spatial_score" in ok.columns
    assert "hypothesis" in ok.columns


def test_run_communication_analysis_pipeline():
    adata = make_communication_demo_adata(n_spots=70, seed=1)
    results = run_communication_analysis(adata, k=6)
    assert results["top_pathway"] is not None
    assert not results["pathway_rankings"].empty
    assert results["hypothesis_label"] == "computational_hypothesis"


def test_diffusion_weighted_signaling():
    adata = make_communication_demo_adata(n_spots=50, seed=2)
    out = compute_diffusion_weighted_signaling(adata, "CXCL12", "CXCR4", k=5)
    assert out is not None
    assert len(out) == adata.n_obs


def test_sender_receiver_network():
    adata = make_communication_demo_adata(n_spots=50, seed=3)
    net = build_sender_receiver_network(adata, ("CXCL12", "CXCR4"), k=5)
    assert "nodes" in net
    assert "edges" in net


def test_niche_signaling_maps():
    adata = make_communication_demo_adata(n_spots=50, seed=4)
    maps = compute_niche_signaling_maps(adata, pairs=[("CXCL12", "CXCR4")])
    assert isinstance(maps, dict)
    assert len(maps) >= 1


def test_generate_communication_report(tmp_path: Path):
    adata = make_communication_demo_adata(n_spots=40, seed=5)
    results = run_communication_analysis(adata)
    path = generate_communication_report(results, tmp_path)
    assert path.exists()
    assert "computational" in path.read_text().lower() or "Communication" in path.read_text()
