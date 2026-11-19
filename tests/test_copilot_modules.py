"""Tests for mbsi.copilot (summaries 12%, report_text 25%, query 28%)."""

from mbsi.copilot.query import QUERY_TEMPLATES, answer_tissue_query
from mbsi.copilot.report_text import generate_methods_text, generate_results_text
from mbsi.copilot.summaries import generate_biological_summary


# --- summaries ---


def test_generate_biological_summary_minimal():
    result = generate_biological_summary({})
    assert "Biological Summary" in result
    assert "validation" in result.lower()


def test_generate_biological_summary_full():
    data = {
        "n_cells": 100,
        "compartments": ["tumor", "stroma"],
        "leakage_score": 0.123,
        "metrics": {"pearson_correlation": 0.87},
    }
    result = generate_biological_summary(data)
    assert "100" in result
    assert "0.1230" in result
    assert "0.8700" in result


def test_generate_biological_summary_partial():
    result = generate_biological_summary({"n_cells": 50})
    assert "50" in result


# --- report_text ---


def test_generate_methods_text():
    params = {"epsilon": 0.05, "gamma": 1.0}
    text = generate_methods_text(params)
    assert "MBSI Studio" in text
    assert "epsilon" in text


def test_generate_results_text_numeric():
    metrics = {"pearson": 0.9, "rmse": 1.23}
    text = generate_results_text(metrics)
    assert "0.9000" in text
    assert "1.2300" in text


def test_generate_results_text_none():
    metrics = {"something": None}
    text = generate_results_text(metrics)
    assert "Results" in text


def test_generate_results_text_string():
    metrics = {"status": "complete"}
    text = generate_results_text(metrics)
    assert "complete" in text


# --- query ---


def test_query_templates_nonempty():
    assert len(QUERY_TEMPLATES) > 0
    assert all(isinstance(t, str) for t in QUERY_TEMPLATES)


def test_answer_boundary_query():
    state = {"boundaries": {"mean_boundary_score": 0.5, "note": "ok"}}
    result = answer_tissue_query("Show tumor-stroma boundary regions.", state)
    assert "0.5" in result


def test_answer_immune_exclusion_query():
    state = {"immune_exclusion": {"mean": 0.3}}
    result = answer_tissue_query("Show immune-excluded niches.", state)
    assert "0.3" in result


def test_answer_compartment_query():
    state = {"compartments": {"labels": ["tumor", "stroma"]}}
    result = answer_tissue_query("Which markers define reconstructed compartments?", state)
    assert "tumor" in result


def test_answer_leakage_query():
    state = {"leakage_score": 0.05}
    result = answer_tissue_query("Which genes show strongest spatial leakage?", state)
    assert "0.05" in result


def test_answer_resistance_query():
    state = {"digital_twin": {"resistance_score": 0.7}}
    result = answer_tissue_query("Which regions may be platinum-resistant?", state)
    assert "0.7" in result


def test_answer_pd1_query():
    state = {"treatment_simulation": {"PD-1 blockade": {"score": 0.2}}}
    result = answer_tissue_query("Simulate PD-1 blockade.", state)
    assert "PD-1" in result


def test_answer_export_query():
    result = answer_tissue_query("Export Nature-style figure package.", {})
    assert "Export" in result


def test_answer_metrics_query():
    state = {"metrics": {"pearson": 0.8}}
    result = answer_tissue_query("Show validation metrics.", state)
    assert "pearson" in result


def test_answer_unknown_query():
    result = answer_tissue_query("What is the meaning of life?", {})
    assert "computed outputs" in result.lower()
