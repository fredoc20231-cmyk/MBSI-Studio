"""Tests for API job persistence."""

import json
from pathlib import Path

import pytest


def test_job_store_save_and_load(tmp_path, monkeypatch):
    from mbsi.api import job_store

    monkeypatch.setattr(job_store, "JOBS_ROOT", tmp_path / "uploads")

    job_id = "test-job-123"
    job_store.save_job(job_id, {
        "status": "uploaded",
        "file_path": "/tmp/data.h5ad",
        "n_spots": 10,
        "n_genes": 5,
    })

    assert job_store.job_exists(job_id)
    meta = job_store.load_job_meta(job_id)
    assert meta["status"] == "uploaded"
    assert meta["n_spots"] == 10

    job_store.update_job(job_id, {"status": "completed", "reconstructed_path": "/tmp/out.h5ad"})
    updated = job_store.load_job_meta(job_id)
    assert updated["status"] == "completed"
    assert updated["reconstructed_path"] == "/tmp/out.h5ad"
