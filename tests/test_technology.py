"""Tests for technology schema catalog."""

from mbsi.schema.technology import (
    ALL_UI_TECHNOLOGY_OPTIONS,
    COMING_LATER_UI_TECHNOLOGY_OPTIONS,
    MILESTONE_1_PLATFORMS,
    TECHNOLOGIES,
    TECHNOLOGY_CATALOG,
    UI_TECHNOLOGY_OPTIONS,
    get_technology,
    list_technologies,
)


def test_milestone_and_full_catalog():
    assert len(MILESTONE_1_PLATFORMS) == 3
    assert len(UI_TECHNOLOGY_OPTIONS) == 3
    assert len(TECHNOLOGY_CATALOG) == 10
    assert len(list_technologies()) == 10
    assert len(ALL_UI_TECHNOLOGY_OPTIONS) == 10


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


def test_coming_later_includes_slide_seq():
    keys = [k for _, k in COMING_LATER_UI_TECHNOLOGY_OPTIONS]
    assert "slide_seq" in keys
