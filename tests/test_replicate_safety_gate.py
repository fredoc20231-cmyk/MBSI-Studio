"""Safety regression tests: spots must never be treated as biological replicates."""
import anndata as ad
import numpy as np
from mbsi.statistics.replicate_aware import run_replicate_aware_tests
from mbsi.differential import run_de


def _data(sample_ids, conditions):
    a = ad.AnnData(X=np.ones((len(sample_ids), 2), dtype=int))
    a.var_names = ["G1", "G2"]
    a.obs["sample_id"] = sample_ids
    a.obs["condition"] = conditions
    return a


def test_single_sample_per_condition_blocks_condition_inference():
    a = _data(["s1"] * 5 + ["s2"] * 5, ["control"] * 5 + ["treated"] * 5)
    result = run_replicate_aware_tests(a)
    assert result["status"] == "blocked"
    assert result["reason"] == "insufficient_biological_replicates"
    assert result["de_results"].empty
    assert run_de(a, mode="condition").empty
    assert run_de(a, mode="pseudobulk").empty


def test_missing_sample_ids_blocks_even_with_many_spots():
    a = _data(["s1", "s2"], ["control", "treated"])
    del a.obs["sample_id"]
    result = run_replicate_aware_tests(a)
    assert result["status"] == "blocked"
    assert result["reason"] == "missing_biological_design"


def test_ambiguous_sample_condition_blocks():
    a = _data(["s1", "s1", "s2", "s3"], ["control", "treated", "control", "treated"])
    result = run_replicate_aware_tests(a)
    assert result["status"] == "blocked"
    assert result["reason"] == "ambiguous_sample_condition"


def test_sufficient_replicates_still_blocks_without_validated_nb_backend():
    a = _data(["s1", "s2", "s3", "s4"], ["control", "control", "treated", "treated"])
    result = run_replicate_aware_tests(a)
    assert result["status"] == "blocked"
    assert result["reason"] == "validated_de_backend_unavailable"
