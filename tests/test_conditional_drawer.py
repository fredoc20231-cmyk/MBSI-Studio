"""Tests for conditional insights drawer."""

from app.components.module_registry import MODULES, DRAWER_MODULES, module_show_drawer, get_module


def test_drawer_only_for_insight_modules():
    expected_drawer = {"discovery", "benchmark", "communication", "tme"}
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
    for key in ("upload", "settings", "project", "notebook", "report", "ai_review"):
        assert key in no_drawer
        assert module_show_drawer(key) is False


def test_intelligence_workflow_order():
    intel = [m for m in MODULES if m.get("section") == "Intelligence"]
    keys = [m["key"] for m in intel]
    assert keys == ["ml_learning", "ai_review"]
    export = [m for m in MODULES if m.get("section") == "Export"]
    export_keys = [m["key"] for m in export]
    assert export_keys.index("notebook") < export_keys.index("report")
    assert export_keys.index("report") < export_keys.index("settings")


def test_notebook_module_registered():
    nb = get_module("notebook")
    assert nb["label"] == "Results Notebook"
    assert nb.get("show_drawer") is False
