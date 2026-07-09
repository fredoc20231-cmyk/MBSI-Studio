"""Tests for Study & Data workspace."""

import importlib


def test_study_data_import():
    mod = importlib.import_module("app.workspaces.study_data")
    assert callable(mod.render)


def test_study_setup_legacy_alias():
    mod = importlib.import_module("app.workspaces.study_setup")
    assert mod.render is not None


def test_technology_options_include_slide_seq():
    from mbsi.schema.technology import ALL_UI_TECHNOLOGY_OPTIONS, get_technology

    keys = [k for _, k in ALL_UI_TECHNOLOGY_OPTIONS]
    assert len(keys) == 10
    assert "slide_seq" in keys
    spec = get_technology("slide_seq")
    assert spec is not None
    assert len(spec.required_files) >= 2
    assert hasattr(spec, "optional_files")
