"""Tests for Results Notebook registry and UI."""

import pandas as pd

from mbsi.reports.registry import (
    clear_registry,
    get_notebook_entries,
    get_registered_outputs,
    register_figure,
    register_finding,
    register_table,
)


def test_register_finding_and_chronological_notebook():
    clear_registry()
    register_finding("Top pathway CXCL12", section="communication", module="communication", title="Top pathway")
    register_table("benchmark", "leaderboard", pd.DataFrame({"method": ["mbsi"], "score": [0.9]}))
    register_figure("discovery", "Benchmark plot", object())

    reg = get_registered_outputs()
    assert len(reg["findings"]) == 1
    assert len(reg["tables"]) == 1
    assert len(reg["figures"]) == 1

    entries = get_notebook_entries()
    assert len(entries) == 3
    assert all("timestamp" in e for e in entries)
    assert all("module" in e for e in entries)
    types = {e["type"] for e in entries}
    assert types == {"finding", "table", "figure"}


def test_notebook_entries_sorted_by_timestamp():
    clear_registry()
    register_finding("first", section="a", module="m1", title="A")
    register_finding("second", section="b", module="m2", title="B")
    entries = get_notebook_entries()
    assert entries[0]["timestamp"] <= entries[1]["timestamp"]


def test_results_notebook_import():
    from app.components.results_notebook import render_results_notebook
    assert callable(render_results_notebook)


def test_clear_registry_clears_notebook():
    clear_registry()
    register_finding("x", section="s", module="m")
    clear_registry()
    assert get_notebook_entries() == []
    assert get_registered_outputs() == {"figures": [], "tables": [], "findings": []}
