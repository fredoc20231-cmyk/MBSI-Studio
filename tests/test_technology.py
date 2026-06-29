"""Tests for technology schema catalog."""

from mbsi.schema.technology import (
    TECHNOLOGIES,
    TECHNOLOGY_CATALOG,
    UI_TECHNOLOGY_OPTIONS,
    get_technology,
    list_technologies,
)


def test_nine_technologies_in_catalog():
    assert len(TECHNOLOGY_CATALOG) == 9
    assert len(UI_TECHNOLOGY_OPTIONS) == 9
    assert len(list_technologies()) == 9


def test_stereo_seq_in_catalog():
    spec = get_technology("stereo_seq")
    assert spec is not None
    assert spec.label == "STOmics Stereo-seq"
    assert "GEF" in spec.required_files[0] or "CGEF" in spec.required_files[0]


def test_stereo_seq_capabilities():
    caps = TECHNOLOGIES["stereo_seq"]
    assert caps["resolution_class"] == "ultra_high"
    assert caps["supports_bins"] is True
    assert caps["supports_cells"] is True
    assert caps["supports_ground_truth_benchmarking"] is True
    assert "qc_metrics" in caps or caps.get("qc_metrics")
