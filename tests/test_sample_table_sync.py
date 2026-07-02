"""Tests for sample table ↔ sample_uploads sync."""

from __future__ import annotations

import pandas as pd

from app.workspaces._sample_upload_state import sync_sample_uploads


def _sample_df(n: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        rows.append(
            {
                "sample_id": f"S{i}",
                "sample_name": f"Sample {i}",
                "patient_id": f"P{i:03d}",
                "condition": "Case",
                "timepoint": "Baseline",
                "replicate_id": "R1",
                "batch_id": "batch1",
                "technology": "10x Visium",
                "file_name": "",
                "tissue_region": "Tumor",
                "notes": "",
            }
        )
    return pd.DataFrame(rows)


def test_sync_creates_upload_entries_for_each_sample():
    df = _sample_df(3)
    uploads = sync_sample_uploads(df, {}, "visium")
    assert set(uploads.keys()) == {"S1", "S2", "S3"}
    assert uploads["S1"]["technology"] == "visium"
    assert uploads["S1"]["status"] == "not_uploaded"


def test_sync_preserves_ingested_state_when_sample_id_kept():
    df = _sample_df(2)
    existing = {
        "S1": {
            "sample_id": "S1",
            "technology": "visium",
            "uploaded_file_name": "visium.zip",
            "status": "ingested",
            "adata_path": "/tmp/S1.h5ad",
            "dataset_id": "ds1",
            "warnings": [],
        }
    }
    uploads = sync_sample_uploads(df, existing, "visium")
    assert uploads["S1"]["status"] == "ingested"
    assert uploads["S1"]["uploaded_file_name"] == "visium.zip"


def test_sync_trims_when_num_samples_reduced():
    df = _sample_df(1)
    existing = {
        "S1": {"sample_id": "S1", "technology": "visium", "status": "not_uploaded"},
        "S2": {"sample_id": "S2", "technology": "visium", "status": "ingested"},
    }
    uploads = sync_sample_uploads(df, existing, "visium")
    assert set(uploads.keys()) == {"S1"}


def test_sync_updates_technology_from_sample_row():
    df = _sample_df(1)
    df.loc[0, "technology"] = "10x Xenium"
    uploads = sync_sample_uploads(df, {}, "visium")
    assert uploads["S1"]["technology"] == "xenium"
