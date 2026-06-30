"""Tests for SVG evidence integration."""

import pandas as pd


def test_svg_to_evidence():
    from mbsi.discovery.spatial_workflow_evidence import svg_to_evidence

    table = pd.DataFrame({
        "gene": ["G1", "G2", "G3"],
        "morans_i": [0.8, 0.6, 0.4],
        "gearys_c": [0.2, 0.3, 0.5],
    })
    store, warnings = svg_to_evidence(table, readiness={"technology_key": "visium"}, run_id="test")
    findings = store.list_findings()
    assert len(findings) >= 1
    assert store.list_evidence()
