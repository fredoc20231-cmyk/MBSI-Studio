"""Tests for archive listing and file inspection."""

import zipfile
from pathlib import Path

from mbsi.io.downloader.archive import extract_archive, is_archive, list_archive_contents
from mbsi.io.downloader.inspector import (
    build_required_file_checklist,
    inspect_downloaded_files,
    update_ingestion_readiness,
)


def _make_synthetic_xenium_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("cell_feature_matrix.h5", b"fake")
        zf.writestr("cells.csv", "cell_id,x,y\n1,0,0\n")
        zf.writestr("spatial/tissue_positions_list.csv", "barcode,in_tissue\n")


def test_archive_list_and_extract(tmp_path):
    zpath = tmp_path / "bundle.zip"
    _make_synthetic_xenium_zip(zpath)
    assert is_archive(zpath)
    names = list_archive_contents(zpath)
    assert "cells.csv" in names
    assert "cell_feature_matrix.h5" in names

    dest = tmp_path / "extracted"
    extracted = extract_archive(zpath, dest)
    assert any("cells.csv" in e for e in extracted)
    assert (dest / "cells.csv").exists()


def test_zip_slip_prevention(tmp_path):
    zpath = tmp_path / "evil.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("../../etc/passwd", "bad")
    dest = tmp_path / "out"
    extracted = extract_archive(zpath, dest)
    assert extracted == []
    assert not (tmp_path / "etc" / "passwd").exists()


def test_inspect_downloaded_files(tmp_path):
    _make_synthetic_xenium_zip(tmp_path / "xenium_outs.zip")
    (tmp_path / "gene_groups.csv").write_text("group\nA\n", encoding="utf-8")
    detection = inspect_downloaded_files(tmp_path)
    assert detection["platform"] in ("xenium", "incomplete", "unknown")
    assert detection["n_local_files"] >= 2


def test_build_required_file_checklist():
    files = ["cell_feature_matrix.h5", "cells.csv", "gene_groups.csv"]
    checklist = build_required_file_checklist("xenium", files)
    assert checklist["platform"] == "xenium"
    assert checklist["n_files"] == 3


def test_update_ingestion_readiness(tmp_path):
    (tmp_path / "cells.csv").write_text("cell_id\n1\n", encoding="utf-8")
    bundle = update_ingestion_readiness(tmp_path)
    assert "readiness" in bundle
    assert "compatibility" in bundle
    assert "score" in bundle["readiness"]
