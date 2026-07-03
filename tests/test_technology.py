"""Tests for technology schema catalog."""

from mbsi.schema.technology import (
    TECHNOLOGIES,
    TECHNOLOGY_CATALOG,
    UI_TECHNOLOGY_OPTIONS,
    get_technology,
    list_technologies,
)


def test_full_technology_catalog():
    # 12 platforms: 3 milestone-1 + 5 functional vendor loaders + 4 coming-later.
    assert len(TECHNOLOGY_CATALOG) == 12
    assert len(list_technologies()) == 12
    # UI_TECHNOLOGY_OPTIONS holds the milestone-1 quick picks; full set is ALL_UI.
    assert len(UI_TECHNOLOGY_OPTIONS) >= 3


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
