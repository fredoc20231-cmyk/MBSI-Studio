"""Tests for mbsi.digital_twin (simulate 29%, state 36%)."""

import anndata as ad
import numpy as np

from mbsi.digital_twin.simulate import compare_treatment_scenarios, simulate_treatment
from mbsi.digital_twin.state import build_tissue_digital_twin
from mbsi.digital_twin.treatment import TREATMENTS


# --- treatment constants ---


def test_treatments_dict():
    assert "untreated" in TREATMENTS
    for name, tx in TREATMENTS.items():
        assert "immune_boost" in tx
        assert "tumor_kill" in tx
        assert "resistance_change" in tx


# --- state ---


def _make_adata(n_obs=30, n_vars=10, seed=0):
    rng = np.random.RandomState(seed)
    adata = ad.AnnData(X=rng.rand(n_obs, n_vars).astype(np.float32))
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    return adata


def test_build_tissue_digital_twin_defaults():
    adata = _make_adata()
    twin = build_tissue_digital_twin(adata)
    assert twin["n_cells"] == 30
    assert twin["n_genes"] == 10
    assert "compartments" in twin
    assert "resistance_score" in twin
    assert "warning" in twin


def test_build_tissue_digital_twin_with_compartments():
    adata = _make_adata()
    adata.obs["compartment"] = ["tumor"] * 15 + ["immune"] * 15
    twin = build_tissue_digital_twin(adata)
    assert "tumor" in twin["compartments"]
    assert "immune" in twin["compartments"]
    np.testing.assert_allclose(twin["compartments"]["tumor"], 0.5)


def test_build_tissue_digital_twin_few_genes():
    adata = _make_adata(n_vars=3)
    twin = build_tissue_digital_twin(adata)
    assert twin["resistance_score"] == 0.3


# --- simulate ---


def test_simulate_treatment_untreated():
    twin = {"compartments": {"tumor": 0.4, "immune": 0.2}, "resistance_score": 0.3}
    result = simulate_treatment(twin, "untreated")
    assert result["treatment"] == "untreated"
    assert result["immune_infiltration_change"] == 0.0
    assert "warning" in result


def test_simulate_treatment_pd1():
    twin = {"compartments": {"tumor": 0.4, "immune": 0.2}, "resistance_score": 0.3}
    result = simulate_treatment(twin, "PD-1 blockade")
    assert result["treatment"] == "PD-1 blockade"
    assert result["immune_infiltration_change"] > 0


def test_simulate_treatment_unknown_falls_to_untreated():
    twin = {"compartments": {"tumor": 0.4, "immune": 0.2}, "resistance_score": 0.3}
    result = simulate_treatment(twin, "nonexistent_drug")
    assert result["treatment"] == "nonexistent_drug"
    assert result["immune_infiltration_change"] == 0.0


def test_simulate_treatment_resistance_clamped():
    twin = {"compartments": {"tumor": 0.4, "immune": 0.2}, "resistance_score": 0.99}
    result = simulate_treatment(twin, "cisplatin")
    assert 0 <= result["predicted_resistance"] <= 1


def test_compare_treatment_scenarios():
    twin = {"compartments": {"tumor": 0.4, "immune": 0.2}, "resistance_score": 0.3}
    result = compare_treatment_scenarios(twin, ["untreated", "cisplatin", "PD-1 blockade"])
    assert "scenarios" in result
    assert len(result["scenarios"]) == 3
    assert "warning" in result
