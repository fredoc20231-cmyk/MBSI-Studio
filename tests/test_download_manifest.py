"""Tests for download manifest schema."""

import json
from pathlib import Path

from mbsi.io.downloader.manifest import DownloadManifest, UrlEntry, load_manifest, save_manifest
from mbsi.io.downloader.manager import create_download_job


def test_manifest_roundtrip(tmp_path):
    manifest = create_download_job(
        "test_project",
        ["https://cf.10xgenomics.com/samples/xenium/gene_groups.csv"],
        tmp_path,
    )
    path = save_manifest(manifest)
    loaded = load_manifest(path)
    assert loaded.job_id == manifest.job_id
    assert loaded.project_id == "test_project"
    assert loaded.status == "queued"
    assert len(loaded.urls) == 1
    assert loaded.urls[0].filename == "gene_groups.csv"


def test_manifest_schema_fields(tmp_path):
    entry = UrlEntry(
        url="https://example.org/a.zip",
        filename="a.zip",
        role="archive",
        technology_hint="xenium",
        source="10x",
        status="complete",
        bytes_downloaded=1000,
        bytes_total=1000,
        local_path=str(tmp_path / "a.zip"),
        sha256="abc123",
    )
    manifest = DownloadManifest(
        job_id="job1",
        project_id="p1",
        created_at="2026-01-01T00:00:00Z",
        status="complete",
        urls=[entry],
        output_dir=str(tmp_path),
        detected_platform="xenium",
        readiness={"score": 55, "status": "partial"},
        compatibility={"qc_preprocess": {"status": "unavailable"}},
        preview={"partial": True, "message": "Partial preview only"},
    )
    data = manifest.to_dict()
    assert data["job_id"] == "job1"
    assert data["urls"][0]["sha256"] == "abc123"
    assert data["detected_platform"] == "xenium"
    assert data["preview"]["partial"] is True

    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    restored = DownloadManifest.from_dict(json.loads(path.read_text()))
    assert restored.readiness["score"] == 55
