"""Security tests for job_id validation and download path containment."""

from __future__ import annotations

import pytest
from fastapi import HTTPException


@pytest.mark.unit
def test_validate_job_id_rejects_traversal():
    from mbsi.api.job_store import InvalidJobIdError, validate_job_id

    for bad in ("../etc/passwd", "job/../secret", "job\\win", "a/b", ""):
        with pytest.raises(InvalidJobIdError):
            validate_job_id(bad)


@pytest.mark.unit
def test_validate_job_id_accepts_uuid_like():
    from mbsi.api.job_store import validate_job_id

    assert validate_job_id("test-job-123") == "test-job-123"


@pytest.mark.unit
def test_resolve_download_path_blocks_escape(tmp_path, monkeypatch):
    from mbsi.api.job_store import InvalidJobIdError, JOBS_ROOT, resolve_download_path

    uploads = tmp_path / "uploads"
    uploads.mkdir()
    allowed = uploads / "job-1" / "reconstructed.h5ad"
    allowed.parent.mkdir(parents=True)
    allowed.write_text("h5ad")

    outside = tmp_path / "outside.h5ad"
    outside.write_text("secret")

    monkeypatch.setattr("mbsi.api.job_store.JOBS_ROOT", uploads)
    resolved = resolve_download_path(str(allowed), allowed_roots=(uploads,))
    assert resolved == allowed.resolve()

    with pytest.raises(InvalidJobIdError):
        resolve_download_path(str(outside), allowed_roots=(uploads,))


@pytest.mark.unit
def test_job_store_rejects_unsafe_job_id(tmp_path, monkeypatch):
    import mbsi.api.job_store as job_store

    monkeypatch.setattr(job_store, "JOBS_ROOT", tmp_path / "uploads")
    with pytest.raises(job_store.InvalidJobIdError):
        job_store.save_job("../evil", {"status": "uploaded"})


@pytest.mark.unit
def test_download_file_rejects_traversal_job_id():
    from mbsi.api.routes import download_file

    with pytest.raises(HTTPException) as exc:
        download_file("../etc/passwd")
    assert exc.value.status_code == 400


@pytest.mark.unit
def test_download_file_rejects_path_outside_uploads(tmp_path, monkeypatch):
    from mbsi.api import job_store
    from mbsi.api.routes import download_file

    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True)
    monkeypatch.setattr(job_store, "JOBS_ROOT", uploads)

    outside = tmp_path / "outside.h5ad"
    outside.write_text("secret")
    job_id = "safe-job"
    job_store.save_job(job_id, {"reconstructed_path": str(outside)})

    with pytest.raises(HTTPException) as exc:
        download_file(job_id)
    assert exc.value.status_code == 403
