"""Tests for SaaS shell, report registry, AI review, ML learning."""

import pandas as pd
import pytest


def test_module_registry():
    from app.components.module_registry import MODULES, MODULE_KEYS, get_module, resolve_module, SECTION_ORDER

    assert len(MODULES) == 16
    assert len(SECTION_ORDER) == 4
    assert "discovery" in MODULE_KEYS
    assert "study_data" in MODULE_KEYS
    assert get_module("discovery")["label"] == "Discovery Intelligence"
    assert get_module("missing")["key"] == "study_data"
    assert resolve_module("project_setup") == "study_data"
    assert resolve_module("preprocess") == "qc_transformation"
    assert resolve_module("study_setup") == "study_data"
    assert resolve_module("spatial_analysis") == "visualization"


def test_report_registry():
    from mbsi.reports.registry import (
        clear_registry,
        get_registered_outputs,
        register_figure,
        register_table,
        register_finding,
        get_notebook_entries,
    )

    clear_registry()
    register_table("test", "demo", pd.DataFrame({"a": [1]}))
    register_figure("test", "fig", object())
    register_finding("finding text", section="test", module="test", title="Finding")
    out = get_registered_outputs()
    assert len(out["tables"]) == 1
    assert len(out["figures"]) == 1
    assert len(out["findings"]) == 1
    assert len(get_notebook_entries()) == 3
    clear_registry()
    assert get_registered_outputs() == {"figures": [], "tables": [], "findings": []}


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
        "registered": {"figures": [], "tables": [], "findings": []},
        "notebook": [],
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
        WORKSPACE_ROUTES,
    )
    from app.components.results_drawer import render_right_results_drawer

    assert len(WORKSPACE_ROUTES) >= 16
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
        "study_data",
        "qc_transformation",
        "visualization",
        "spatial_variable_genes",
        "spatial_gene_sets",
        "spatial_domains",
        "phenotyping",
        "differential_analysis",
        "spatial_gradients",
        "segment_register",
        "reconstruction",
        "benchmark",
        "discovery",
        "ai_review",
        "report_export",
        "settings",
    ]
    import importlib

    for k in keys:
        mod = importlib.import_module(f"app.workspaces.{k}")
        assert callable(mod.render)


def test_legacy_workspace_redirects():
    import importlib

    for legacy in ("project_setup", "preprocess", "notebook", "report", "communication", "tme", "study_setup", "qc_preprocess", "spatial_analysis"):
        mod = importlib.import_module(f"app.workspaces.{legacy}")
        assert callable(mod.render)


def test_theme_module(monkeypatch):
    from app.components.theme import (
        THEME_PALETTES,
        apply_plotly_theme,
        get_plotly_theme_colors,
        VALID_THEMES,
        THEME_KEY,
    )

    assert VALID_THEMES == ("dark", "light")
    assert "plot_paper" in THEME_PALETTES["light"]
    assert THEME_PALETTES["light"]["bg"] == "#f8fafc"
    assert THEME_PALETTES["dark"]["bg"] == "#0c1117"

    class _FakeFig:
        def __init__(self):
            self.kwargs = {}

        def update_layout(self, **kwargs):
            self.kwargs.update(kwargs)

    class _FakeState(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import app.components.theme as theme_mod

    monkeypatch.setattr(theme_mod.st, "session_state", _FakeState({THEME_KEY: "dark"}))

    fig = _FakeFig()
    apply_plotly_theme(fig)
    assert fig.kwargs["paper_bgcolor"] == THEME_PALETTES["dark"]["plot_paper"]

    colors = get_plotly_theme_colors()
    assert colors["plot_font"] == THEME_PALETTES["dark"]["plot_font"]
