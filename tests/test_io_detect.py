"""Tests for mbsi.io platform detection."""

from mbsi.io.detect import detect_platform


def test_detect_visium_from_names():
    names = [
        "filtered_feature_bc_matrix.h5",
        "spatial/tissue_positions_list.csv",
        "spatial/scalefactors_json.json",
    ]
    d = detect_platform(names)
    assert d["platform"] == "visium"
    assert "count_matrix" in d["required_found"]
    assert d["confidence"] >= 0.85


def test_detect_h5ad():
    d = detect_platform(["sample.h5ad"])
    assert d["platform"] == "generic_h5ad"
    assert d["confidence"] >= 0.8


def test_detect_csv_matrix():
    d = detect_platform(["matrix.csv", "coordinates.csv"])
    assert d["platform"] in ("csv_matrix", "generic_h5ad")


def test_detect_xenium():
    d = detect_platform(["cell_feature_matrix.h5", "cells.csv"])
    assert d["platform"] == "xenium"


def test_detect_stereo_seq():
    d = detect_platform(["expression.gef", "coordinates.csv", "saw/report.html"])
    assert d["platform"] == "stereo_seq"
    assert d["confidence"] >= 0.5


def test_detect_unknown():
    d = detect_platform(["random.txt"])
    assert d["platform"] == "unknown"
    assert d["confidence"] == 0.0


def test_detect_incomplete():
    d = detect_platform(["counts.csv"])
    assert d["platform"] == "incomplete"
    assert "spatial_coordinates_or_positions" in d["missing"]
