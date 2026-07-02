"""Tests for per-sample upload state and ingest helpers."""

from __future__ import annotations

import pandas as pd

from app.workspaces._sample_upload_state import (
    apply_ingestion_to_session,
    can_start_analysis,
    default_sample_upload_entry,
    ingest_sample_file,
    required_files_for_technology,
    resolve_sample_technology,
)
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def test_default_sample_upload_entry_shape():
    entry = default_sample_upload_entry("S1", "xenium")
    assert entry["sample_id"] == "S1"
    assert entry["technology"] == "xenium"
    assert entry["status"] == "not_uploaded"
    assert entry["warnings"] == []


def test_resolve_sample_technology_from_label():
    assert resolve_sample_technology("10x Visium", "") == "visium"
    assert resolve_sample_technology("Generic AnnData / CSV", "") == "generic_h5ad"
    assert resolve_sample_technology("", "xenium") == "xenium"


def test_required_files_for_milestone_platforms():
    visium_req = required_files_for_technology("visium")
    xenium_req = required_files_for_technology("xenium")
    assert any("feature" in f.lower() or "matrix" in f.lower() for f in visium_req)
    assert any("cell_feature" in f for f in xenium_req)


def test_can_start_analysis_gating():
    meta = {"project_title": "Test study"}
    samples = pd.DataFrame([{"sample_id": "S1"}])
    uploads = {"S1": {"status": "ingested"}}
    ok, missing = can_start_analysis(meta, samples, uploads, "visium")
    assert ok is True
    assert missing == []

    ok2, missing2 = can_start_analysis({}, samples, uploads, "visium")
    assert ok2 is False
    assert "project title or biological question" in missing2[0]


def test_ingest_sample_file_xenium(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=12, n_genes=30)
    result = ingest_sample_file(
        tmp_path,
        sample_id="S1",
        technology_key="xenium",
        uploaded_file_name="xenium_bundle.zip",
    )
    assert result["status"] == "ingested"
    assert result["sample_id"] == "S1"
    assert result["adata_path"]
    assert result["adata"].n_obs >= 5
    assert result["adata"].obs["sample_id"].iloc[0] == "S1"


def test_apply_ingestion_single_sample_sets_global_adata():
    fake = {"sample_id": "S1", "technology": "xenium", "adata": object(), "platform": "xenium"}
    updates = apply_ingestion_to_session(fake, num_samples=1)
    assert "adata" in updates
    assert "ingestion_result" in updates


def test_apply_ingestion_multi_sample_uses_sample_adatas():
    fake = {
        "sample_id": "S2",
        "technology": "visium",
        "adata": object(),
        "adata_path": "/tmp/S2.h5ad",
        "platform": "visium",
    }
    updates = apply_ingestion_to_session(fake, num_samples=3)
    assert "sample_adatas" in updates
    assert "S2" in updates["sample_adatas"]
    assert "adata" not in updates
