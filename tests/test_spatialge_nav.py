"""Tests for 16-module spatialGE navigation."""

from app.components.module_registry import (
    LEGACY_MODULE_ALIASES,
    MODULES,
    MODULE_KEYS,
    SECTION_ORDER,
    get_module,
    resolve_module,
)


def test_sixteen_modules():
    assert len(MODULES) == 16
    assert len(MODULE_KEYS) == 16


def test_four_sections():
    sections = {m["section"] for m in MODULES}
    assert sections == set(SECTION_ORDER)
    assert SECTION_ORDER == ["Setup", "Core Spatial Analysis", "MBSI Intelligence", "Export"]


def test_section_counts():
    grouped = {}
    for m in MODULES:
        grouped.setdefault(m["section"], []).append(m["key"])
    assert len(grouped["Setup"]) == 2
    assert len(grouped["Core Spatial Analysis"]) == 7
    assert len(grouped["MBSI Intelligence"]) == 5
    assert len(grouped["Export"]) == 2


def test_default_module():
    assert MODULE_KEYS[0] == "study_data"
    assert get_module("study_data")["label"] == "Study & Data"


def test_legacy_aliases():
    assert resolve_module("study_setup") == "study_data"
    assert resolve_module("qc_preprocess") == "qc_transformation"
    assert resolve_module("spatial_analysis") == "visualization"
    assert LEGACY_MODULE_ALIASES["project_setup"] == "study_data"


def test_mbsi_moat_order():
    assert MODULE_KEYS.index("spatial_gradients") < MODULE_KEYS.index("segment_register")
    intel_keys = [m["key"] for m in MODULES if m["section"] == "MBSI Intelligence"]
    assert intel_keys == [
        "segment_register",
        "reconstruction",
        "benchmark",
        "discovery",
        "ai_review",
    ]
