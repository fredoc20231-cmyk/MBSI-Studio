"""Tests for Seurat-like evidence builder."""

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.seurat_like import run_seurat_like_pipeline
from mbsi.discovery.seurat_evidence import build_seurat_evidence


def test_build_seurat_evidence():
    adata = make_synthetic_visium_adata(n_spots=40, n_genes=80, seed=9)
    results = run_seurat_like_pipeline(
        adata,
        min_counts=0,
        min_genes=0,
        max_mito=100,
        n_top_genes=40,
        n_comps=10,
        n_neighbors=10,
        n_pcs=5,
        resolution=0.8,
    )
    readiness = {"sample_metadata": [{"sample_id": "S1", "condition": "ctrl", "replicate_id": "1"}]}
    store, warnings = build_seurat_evidence(results, readiness=readiness, run_id="test-run")
    findings = store.list_findings()
    assert len(findings) >= 1
    assert any("QC" in f.title or "Marker" in f.title or "cluster" in f.title.lower() for f in findings)
