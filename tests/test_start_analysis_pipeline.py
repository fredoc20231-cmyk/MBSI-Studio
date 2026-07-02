"""Tests for Start Analysis / run_milestone1_pipeline integration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.workspaces._sample_upload_state import can_start_analysis, get_primary_ingested_sample
from mbsi.io.xenium import load_xenium
from mbsi.workflows.milestone1_pipeline import run_milestone1_pipeline
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def test_run_milestone1_pipeline_returns_expected_keys(tmp_path):
    write_mini_xenium_bundle(tmp_path / "bundle", n_cells=20, n_genes=40)
    adata, _ = load_xenium(tmp_path / "bundle")
    out_dir = tmp_path / "m1_out"

    result = run_milestone1_pipeline(
        adata,
        params={
            "platform": "xenium",
            "output_dir": out_dir,
            "min_counts": 5,
            "min_genes": 3,
            "max_mito": 100.0,
            "min_cells_per_gene": 2,
        },
    )

    assert result["status"] == "success"
    for key in ("qc_summary", "normalization", "embedding", "clusters", "markers", "spatial", "warnings"):
        assert key in result
    assert result["embedding"]["has_umap"] is True
    assert result["clusters"]["n_clusters"] >= 1
    assert result["spatial"]["has_spatial"] is True
    assert Path(result["output_paths"]["processed_h5ad"]).exists()


def test_start_analysis_enablement_with_ingested_sample():
    meta = {"biological_question": "Spatial niches?"}
    samples = pd.DataFrame([{"sample_id": "S1", "sample_name": "A"}])
    uploads = {
        "S1": {
            "sample_id": "S1",
            "technology": "xenium",
            "status": "ingested",
            "adata_path": "/tmp/x.h5ad",
            "uploaded_file_name": "x.zip",
        }
    }
    ok, missing = can_start_analysis(meta, samples, uploads, "xenium")
    assert ok is True
    sid, primary = get_primary_ingested_sample(uploads)
    assert sid == "S1"
    assert primary["status"] == "ingested"
