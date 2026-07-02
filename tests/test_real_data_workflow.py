"""End-to-end Milestone 1 workflow on synthetic Visium/Xenium AnnData."""

from __future__ import annotations

import numpy as np

from mbsi.analysis.seurat_like import run_seurat_like_pipeline
from mbsi.domains import detect_domains
from mbsi.io.visium import load_space_ranger
from mbsi.io.xenium import load_xenium
from mbsi.spatial_stats import spatial_autocorrelation_table
from mbsi.workflows.report import run_report_workflow
from tests.test_visium_ingestion import write_mini_spaceranger
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def _run_milestone_pipeline(adata, *, filter_tissue: bool = False):
    results = run_seurat_like_pipeline(
        adata,
        preset="spatial_transcriptomics",
        min_counts=10,
        min_genes=5,
        max_mito=50.0,
        filter_tissue=filter_tissue,
    )
    out = results["adata"]
    assert out.n_obs >= 5
    assert "cluster" in out.obs.columns
    assert "X_umap" in out.obsm
    markers = results.get("markers")
    assert markers is not None
    assert len(markers) > 0

    svg = spatial_autocorrelation_table(out, n_top=30, k=4)
    assert len(svg) > 0
    assert "morans_i" in svg.columns or "gene" in svg.columns

    domain_adata, summary, _ = detect_domains(out, method="leiden", resolution=0.6)
    assert "domain" in domain_adata.obs.columns
    assert len(summary) > 0

    coords = out.obsm["spatial"]
    assert coords.shape == (out.n_obs, 2)
    assert not np.isnan(coords).any()
    return out, results


def test_real_data_workflow_visium(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=20, n_genes=50)
    adata, meta = load_space_ranger(tmp_path)
    assert meta["platform"] == "visium"
    assert meta["readiness_score"] >= 50
    _run_milestone_pipeline(adata, filter_tissue=False)


def test_real_data_workflow_xenium(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=20, n_genes=50)
    adata, meta = load_xenium(tmp_path)
    assert meta["platform"] == "xenium"
    assert "x_centroid" in adata.obs.columns
    assert meta["readiness_score"] >= 50
    _run_milestone_pipeline(adata)


def test_real_data_report_export(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=20, n_genes=50)
    adata, meta = load_space_ranger(tmp_path)
    out, results = _run_milestone_pipeline(adata)
    snapshot = {
        "mbsi_platform": meta["platform"],
        "dataset_readiness": meta.get("readiness", {}),
        "analysis_results": {"n_obs": out.n_obs, "n_clusters": out.obs["cluster"].nunique()},
        "marker_table": results.get("markers"),
        "using_synthetic_demo": False,
        "registered": {"figures": [], "tables": [], "findings": []},
        "notebook": [],
    }
    record = run_report_workflow(tmp_path / "reports", snapshot=snapshot, export_type="html")
    assert record.status == "success"
    assert record.outputs.get("path")
    assert (tmp_path / "reports").exists()
