"""Tests for sender/receiver ranking and diffusion flux."""

from mbsi.communication import (
    rank_sender_receiver,
    compute_diffusion_flux,
    build_niche_interaction_map,
    make_communication_demo_adata,
)


def test_rank_sender_receiver():
    adata = make_communication_demo_adata(n_spots=50, seed=0)
    out = rank_sender_receiver(adata, ("CXCL12", "CXCR4"), k=5)
    assert not out["table"].empty
    assert not out["edges"].empty
    assert "sender_score" in out["table"].columns


def test_compute_diffusion_flux():
    adata = make_communication_demo_adata(n_spots=40, seed=1)
    flux = compute_diffusion_flux(adata, "CXCL12", "CXCR4", k=5)
    assert flux.shape[0] == adata.n_obs
    assert flux.max() <= 1.0 + 1e-6


def test_build_niche_interaction_map():
    adata = make_communication_demo_adata(n_spots=40, seed=2)
    m = build_niche_interaction_map(adata, ("VEGFA", "KDR"))
    assert len(m["x"]) == adata.n_obs
    assert "flux" in m
