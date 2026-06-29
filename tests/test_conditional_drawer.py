"""Tests for conditional insights drawer."""

from app.components.module_registry import MODULES, DRAWER_MODULES, module_show_drawer, get_module, resolve_module


def test_drawer_only_for_insight_modules():
    expected_drawer = {"discovery", "benchmark"}
    assert DRAWER_MODULES == expected_drawer
    for mod in MODULES:
        key = mod["key"]
        assert mod.get("show_drawer") is module_show_drawer(key)
        if key in expected_drawer:
            assert module_show_drawer(key) is True
        else:
            assert module_show_drawer(key) is False


def test_no_drawer_modules_full_width():
    no_drawer = [m["key"] for m in MODULES if not m.get("show_drawer")]
    for key in ("study_setup", "settings", "report_export", "ai_review", "qc_preprocess"):
        assert key in no_drawer
        assert module_show_drawer(key) is False


def test_intelligence_workflow_order():
    intel = [m for m in MODULES if m.get("section") == "Intelligence"]
    keys = [m["key"] for m in intel]
    assert keys == ["ai_review"]
    export = [m for m in MODULES if m.get("section") == "Export"]
    export_keys = [m["key"] for m in export]
    assert export_keys.index("report_export") < export_keys.index("settings")


def test_report_export_module_registered():
    mod = get_module("report_export")
    assert mod["label"] == "Report & Export"
    assert mod.get("show_drawer") is False


def test_legacy_module_resolution():
    assert resolve_module("notebook") == "report_export"
    assert resolve_module("segmentation") == "segment_register"
