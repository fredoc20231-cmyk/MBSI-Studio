"""Tests for SaaS shell, report registry, AI review, ML learning."""

import pandas as pd
import pytest


def test_module_registry():
    from app.components.module_registry import MODULES, MODULE_KEYS, get_module

    assert len(MODULES) == 14
    assert "discovery" in MODULE_KEYS
    assert get_module("discovery")["label"] == "Discovery"
    assert get_module("missing")["key"] == "project"


def test_report_registry():
    from mbsi.reports.registry import (
        clear_registry,
        get_registered_outputs,
        register_figure,
        register_table,
    )

    clear_registry()
    register_table("test", "demo", pd.DataFrame({"a": [1]}))
    register_figure("test", "fig", object())
    out = get_registered_outputs()
    assert len(out["tables"]) == 1
    assert len(out["figures"]) == 1
    clear_registry()
    assert get_registered_outputs() == {"figures": [], "tables": []}


def test_final_report(tmp_path):
    from mbsi.reports.final_report import (
        create_data_bundle,
        generate_final_html_report,
        generate_final_pdf_report,
    )

    snap = {
        "benchmark_results": {"readiness_score": 80},
        "communication_results": None,
        "tme_results": None,
        "discovery_results": None,
        "last_run": "test",
        "registered": {"figures": [], "tables": []},
    }
    html = generate_final_html_report(tmp_path, snapshot=snap)
    pdf = generate_final_pdf_report(tmp_path, snapshot=snap)
    bundle = create_data_bundle(tmp_path, snapshot=snap)
    assert html.exists()
    assert pdf.exists()
    assert bundle.exists()


def test_ai_review():
    from mbsi.ai_review.reviewer import answer_outcome_question

    ans = answer_outcome_question("what is the top benchmark method?")
    assert "clinical decision support" in ans.lower() or "Grounded" in ans or "pipeline" in ans.lower()


def test_ml_learning():
    from mbsi.ml_learning.recommender import recommend_next_analysis, record_user_feedback
    from mbsi.ml_learning.run_store import log_analysis_run, load_runs

    recs = recommend_next_analysis("benchmark")
    assert len(recs) >= 1
    log_analysis_run("benchmark", "unit-test", {"test": True})
    runs = load_runs(limit=5)
    assert isinstance(runs, list)
    record_user_feedback("benchmark", 4)


def test_saas_shell_imports():
    from app.components.saas_shell import (
        init_saas_state,
        render_left_main_nav,
        render_main_workspace,
        render_saas_app,
        render_top_context_bar,
    )
    from app.components.results_drawer import render_right_results_drawer

    for fn in (
        init_saas_state,
        render_left_main_nav,
        render_top_context_bar,
        render_main_workspace,
        render_right_results_drawer,
        render_saas_app,
    ):
        assert callable(fn)


def test_workspace_imports():
    keys = [
        "project", "upload", "preprocess", "segmentation", "reconstruction",
        "spatial_analysis", "benchmark", "communication", "tme", "discovery",
        "ml_learning", "ai_review", "report", "settings",
    ]
    import importlib

    for k in keys:
        mod = importlib.import_module(f"app.workspaces.{k}")
        assert callable(mod.render)
