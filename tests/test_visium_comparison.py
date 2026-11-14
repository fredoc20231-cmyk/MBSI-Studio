"""Regression tests for observed-data Visium multi-sample comparison."""
import numpy as np
import pytest
import anndata as ad
from scipy.sparse import csr_matrix
from mbsi.analysis.visium_comparison import (
    combine_visium_samples, per_sample_qc, compare_gene_expression
)


def sample(counts, genes=("A", "B"), spatial=True):
    a = ad.AnnData(X=csr_matrix(np.asarray(counts)))
    a.var_names = list(genes)
    a.obs_names = [f"spot{i}" for i in range(a.n_obs)]
    if spatial:
        a.obsm["spatial"] = np.column_stack((np.arange(a.n_obs), np.arange(a.n_obs)))
    return a


def test_combine_preserves_sample_identity_and_counts():
    a = sample([[1, 0], [0, 2]])
    b = sample([[3, 4]])
    merged = combine_visium_samples({"s1": a, "s2": b})
    assert merged.n_obs == 3
    assert merged.n_vars == 2
    assert set(merged.obs["sample_id"]) == {"s1", "s2"}
    assert merged.layers["counts"].sum() == 10
    assert per_sample_qc(merged).set_index("sample_id").loc["s1", "n_spots"] == 2
    assert compare_gene_expression(merged, "A").set_index("sample_id").loc["s2", "mean_counts"] == 3


def test_rejects_missing_spatial_and_noncounts():
    with pytest.raises(ValueError, match="spatial"):
        combine_visium_samples({"a": sample([[1]], genes=("A",), spatial=False),
                                "b": sample([[2]], genes=("A",))})
    with pytest.raises(ValueError, match="raw counts"):
        combine_visium_samples({"a": sample([[1.5]], genes=("A",)),
                                "b": sample([[2]], genes=("A",))})


def test_shared_genes_only():
    merged = combine_visium_samples({
        "a": sample([[1, 2]], genes=("A", "B")),
        "b": sample([[3, 4]], genes=("B", "C")),
    })
    assert merged.var_names.tolist() == ["B"]
    assert merged.layers["counts"].sum() == 5


def test_requires_two_samples():
    with pytest.raises(ValueError, match="two samples"):
        combine_visium_samples({"only": sample([[1]], genes=("A",))})


def test_pseudobulk_sums_raw_counts_by_sample():
    from mbsi.analysis.visium_comparison import pseudobulk_counts
    merged = combine_visium_samples({
        "a": sample([[1, 2], [3, 4]]),
        "b": sample([[5, 6]]),
    })
    bulk, metadata = pseudobulk_counts(merged)
    assert bulk.n_obs == 2
    assert bulk.n_vars == 2
    assert metadata.set_index("sample_id").loc["a", "n_spots"] == 2
    totals = {sid: int(bulk.X[i].sum()) for i, sid in enumerate(bulk.obs["sample_id"])}
    assert totals == {"a": 10, "b": 11}


def test_pseudobulk_requires_raw_counts_and_complete_metadata():
    from mbsi.analysis.visium_comparison import pseudobulk_counts
    a = sample([[1, 2]])
    a.obs["sample_id"] = "s1"
    with pytest.raises(ValueError, match="Raw counts"):
        pseudobulk_counts(a)
    a.layers["counts"] = a.X.copy()
    with pytest.raises(ValueError, match="Missing metadata"):
        pseudobulk_counts(a, group_keys=("patient_id",))
