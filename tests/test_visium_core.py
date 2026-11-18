import numpy as np
import pandas as pd
import pytest

from mbsi.visium_core import MODULE_NAMES, capabilities, run_visium_module
from mbsi.visium_core.provenance import BlockedAnalysis, facts_gate
from mbsi.visium_core.replicate_de import replicate_check
from mbsi.visium_core.spatial import bh_fdr
from mbsi.visium_core.visium_hd import rebin_coordinates


def test_bh_fdr_matches_reference():
    p = np.array([0.01, 0.04, 0.03, 0.2])
    np.testing.assert_allclose(bh_fdr(p), [0.04, 0.16 / 3, 0.16 / 3, 0.2])


def test_de_blocked_with_one_replicate():
    design = pd.DataFrame({"sample": ["a", "b", "c"], "condition": ["ctrl", "tumor", "tumor"]})
    with pytest.raises(BlockedAnalysis):
        replicate_check(design, "condition")


def test_de_allowed_with_two_replicates():
    design = pd.DataFrame({"sample": list("abcd"), "condition": ["c", "c", "t", "t"]})
    assert replicate_check(design, "condition") == {"c": 2, "t": 2}


def test_hd_bins_16um():
    keys = rebin_coordinates(np.array([[0, 0], [15.9, 15.9], [16, 0]]), 16)
    assert keys.tolist() == [[0, 0], [0, 0], [1, 0]]


def test_hd_rejects_unsupported_bin():
    with pytest.raises(BlockedAnalysis):
        rebin_coordinates(np.zeros((1, 2)), 5)


def test_missing_dataset_is_blocked_not_fabricated():
    out = run_visium_module("visium_svg", None, {})
    assert out["status"] == "blocked" and "outputs" not in out


def test_capabilities_list_every_module():
    assert {c["module"] for c in capabilities()} == set(MODULE_NAMES)


def test_facts_gate_rejects_blocked_claim():
    probs = facts_gate([{"text": "x", "source_module": "visium_cci", "field": "colocalized_pairs"}], {"visium_cci": {"status": "blocked"}})
    assert probs
