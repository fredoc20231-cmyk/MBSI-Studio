"""End-to-end Milestone 1 workflow on synthetic Visium/Xenium AnnData."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from mbsi.domains import detect_domains
from mbsi.io.visium import load_space_ranger
from mbsi.io.xenium import load_xenium
from mbsi.workflows.report import run_report_workflow
from mbsi.workflows.xenium_pipeline import run_visium_milestone_pipeline, run_xenium_milestone_pipeline
from tests.test_visium_ingestion import write_mini_spaceranger
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def _run_milestone_pipeline(adata, output_dir: Path, *, platform: str, filter_tissue: bool = False):
    if platform == "xenium":
        result = run_xenium_milestone_pipeline(
            adata,
            output_dir,
            min_counts=10,
            min_genes=5,
            max_mito=50.0,
            min_cells_per_gene=2,
            filter_tissue=filter_tissue,
            spatial_stats_top_n=30,
        )
    else:
        result = run_visium_milestone_pipeline(
            adata,
            output_dir,
            min_counts=10,
            min_genes=5,
            max_mito=50.0,
            min_cells_per_gene=2,
            filter_tissue=filter_tissue,
            spatial_stats_top_n=30,
        )
    out = result["adata"]
    assert out.n_obs >= 5
    assert "cluster" in out.obs.columns
    assert "X_umap" in out.obsm
    markers = result.get("markers")
    assert markers is not None
    assert len(markers) > 0

    svg = result["spatial_stats"]
    assert len(svg) > 0
    assert "morans_i" in svg.columns or "gene" in svg.columns
    assert Path(result["output_paths"]["processed_h5ad"]).exists()

    domain_adata, summary, _ = detect_domains(out, method="leiden", resolution=0.6)
    assert "domain" in domain_adata.obs.columns
    assert len(summary) > 0

    coords = out.obsm["spatial"]
    assert coords.shape == (out.n_obs, 2)
    assert not np.isnan(coords).any()
    return out, result


def test_real_data_workflow_visium(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=20, n_genes=50)
    adata, meta = load_space_ranger(tmp_path)
    assert meta["platform"] == "visium"
    assert meta["readiness_score"] >= 50
    _run_milestone_pipeline(adata, tmp_path / "visium_pipeline", platform="visium", filter_tissue=False)


def test_real_data_workflow_xenium(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=20, n_genes=50)
    adata, meta = load_xenium(tmp_path)
    assert meta["platform"] == "xenium"
    assert "x_centroid" in adata.obs.columns
    assert meta["readiness_score"] >= 50
    _run_milestone_pipeline(adata, tmp_path / "xenium_pipeline", platform="xenium")


def test_real_data_report_export(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=20, n_genes=50)
    adata, meta = load_space_ranger(tmp_path)
    out, results = _run_milestone_pipeline(
        adata, tmp_path / "visium_pipeline", platform="visium", filter_tissue=False
    )
    snapshot = {
        "mbsi_platform": meta["platform"],
        "dataset_readiness": meta.get("readiness", {}),
        "analysis_results": {"n_obs": out.n_obs, "n_clusters": out.obs["cluster"].nunique()},
        "marker_table": results.get("markers"),
        "spatial_stats": results.get("spatial_stats"),
        "using_synthetic_demo": False,
        "registered": {"figures": [], "tables": [], "findings": []},
        "notebook": [],
    }
    record = run_report_workflow(tmp_path / "reports", snapshot=snapshot, export_type="html")
    assert record.status == "success"
    assert record.outputs.get("path")
    assert (tmp_path / "reports").exists()
    assert results["output_paths"].get("report_html") or (tmp_path / "visium_pipeline" / "reports").exists()
