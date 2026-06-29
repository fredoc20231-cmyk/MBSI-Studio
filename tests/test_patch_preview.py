"""Tests for patch preview analysis."""

from pathlib import Path

import pandas as pd

from mbsi.io.downloader.manifest import DownloadManifest, UrlEntry
from mbsi.io.downloader.patch_analyzer import (
    PARTIAL_MESSAGE,
    run_incremental_patch_analysis,
    run_patch_preview_analysis,
    select_preview_patch,
)


def test_select_preview_patch_coordinates(tmp_path):
    coords = tmp_path / "cells.csv"
    coords.write_text("cell_id,x,y\n1,1.0,2.0\n2,3.0,4.0\n3,5.0,6.0\n", encoding="utf-8")
    patch = select_preview_patch(tmp_path)
    assert patch["patch_type"] == "coordinates"
    assert patch.get("patch_coords") is not None


def test_run_patch_preview_partial_status(tmp_path):
    (tmp_path / "gene_groups.csv").write_text("g\nA\n", encoding="utf-8")
    preview = run_patch_preview_analysis(tmp_path)
    assert preview["partial"] is True
    assert preview["message"] == PARTIAL_MESSAGE
    assert "completeness" in preview


def test_run_incremental_patch_analysis():
    manifest = DownloadManifest(
        job_id="j1",
        project_id="p1",
        created_at="2026-01-01T00:00:00Z",
        status="running",
        urls=[
            UrlEntry(
                url="https://example.org/a.csv",
                filename="a.csv",
                status="complete",
                local_path="/tmp/a.csv",
            ),
            UrlEntry(
                url="https://example.org/b.csv",
                filename="b.csv",
                status="queued",
            ),
        ],
        output_dir=str(Path("/nonexistent")),
    )
    preview = run_incremental_patch_analysis(manifest)
    assert preview["partial"] is True
    assert preview["n_complete"] == 1
    assert preview["n_total"] == 2
