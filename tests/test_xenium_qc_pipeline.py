"""Full Xenium QC → cluster → markers → spatial stats pipeline test."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mbsi.analysis.xenium_qc import compute_xenium_qc_metrics, run_xenium_qc, xenium_qc_summary
from mbsi.io.xenium import load_xenium
from mbsi.workflows.xenium_pipeline import run_xenium_milestone_pipeline, run_visium_milestone_pipeline
from tests.test_visium_ingestion import write_mini_spaceranger
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def test_xenium_qc_metrics(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=20, n_genes=40)
    adata, _ = load_xenium(tmp_path)
    adata = compute_xenium_qc_metrics(adata)
    assert "total_counts" in adata.obs.columns
    assert "n_genes_by_counts" in adata.obs.columns
    assert "x_centroid" in adata.obs.columns
    assert adata.uns["xenium_qc"]["has_cell_boundaries"] is False
    assert "spatial_coverage" in adata.uns["xenium_qc"]
    summary = xenium_qc_summary(adata)
    assert not summary.empty


def test_xenium_qc_filtering(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=20, n_genes=40)
    adata, _ = load_xenium(tmp_path)
    filtered, summary, warnings = run_xenium_qc(
        adata,
        min_counts=1,
        min_genes=1,
        max_mito=100.0,
        min_cells_per_gene=1,
    )
    assert filtered.n_obs >= 5
    assert filtered.n_vars >= 5
    assert "qc_pass" not in filtered.obs.columns or filtered.obs["qc_pass"].all()
    assert not summary.empty


def test_xenium_milestone_pipeline(tmp_path):
    write_mini_xenium_bundle(tmp_path / "bundle", n_cells=24, n_genes=50)
    adata, meta = load_xenium(tmp_path / "bundle")
    assert meta["platform"] == "xenium"

    out_dir = tmp_path / "outputs"
    result = run_xenium_milestone_pipeline(
        adata,
        out_dir,
        min_counts=5,
        min_genes=3,
        max_mito=100.0,
        min_cells_per_gene=2,
        spatial_stats_top_n=20,
    )

    out = result["adata"]
    assert out.n_obs >= 5
    assert "cluster" in out.obs.columns
    assert "X_umap" in out.obsm
    assert result["markers"] is not None and len(result["markers"]) > 0
    assert not result["spatial_stats"].empty
    assert "morans_i" in result["spatial_stats"].columns

    paths = result["output_paths"]
    assert Path(paths["processed_h5ad"]).exists()
    assert Path(paths["cluster_labels_csv"]).exists()
    assert Path(paths["cell_type_annotations_csv"]).exists()
    assert Path(paths["cluster_markers_csv"]).exists()
    assert Path(paths["qc_summary_csv"]).exists()
    assert Path(paths["spatial_autocorrelation_csv"]).exists()
    if "report_html" in paths:
        assert Path(paths["report_html"]).exists()

    clusters = pd.read_csv(paths["cluster_labels_csv"])
    assert len(clusters) == out.n_obs
    annotations = pd.read_csv(paths["cell_type_annotations_csv"])
    assert "cell_type" in annotations.columns


def test_xenium_transcript_density_optional(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=10, n_genes=20)
    adata, _ = load_xenium(tmp_path)
    cell_ids = adata.obs_names.tolist()
    tx_rows = []
    for cid in cell_ids:
        for _ in range(5):
            tx_rows.append({"cell_id": cid, "gene": "GENE0"})
    pd.DataFrame(tx_rows).to_parquet(tmp_path / "transcripts.parquet")
    adata.uns.setdefault("xenium", {}).setdefault("optional_artifacts", {})["transcripts"] = str(
        tmp_path / "transcripts.parquet"
    )
    adata = compute_xenium_qc_metrics(adata)
    assert adata.uns["xenium_qc"]["has_transcripts"] is True
    assert adata.obs["transcript_density"].notna().all()
    assert (adata.obs["transcript_density"] >= 5).all()


def test_visium_milestone_pipeline(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=18, n_genes=45, with_h5=True)
    from mbsi.io.visium import load_space_ranger

    adata, meta = load_space_ranger(tmp_path)
    assert meta["platform"] == "visium"

    out_dir = tmp_path / "visium_out"
    result = run_visium_milestone_pipeline(
        adata,
        out_dir,
        min_counts=5,
        min_genes=3,
        max_mito=100.0,
        min_cells_per_gene=2,
        filter_tissue=False,
        spatial_stats_top_n=15,
    )
    assert result["adata"].n_obs >= 5
    assert Path(result["output_paths"]["processed_h5ad"]).exists()
    coords = result["adata"].obsm["spatial"]
    assert coords.shape == (result["adata"].n_obs, 2)
    assert not np.isnan(coords).any()
