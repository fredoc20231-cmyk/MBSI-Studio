"""Regression tests for the production spatial browser data contract."""
import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix
import anndata as ad

from mbsi.visualization.browser_contract import (
    AnnDataBrowserAdapter, resolve_browser_samples,
)


def _sample(matrix, genes=("CD8A", "TP53"), sid="a"):
    a = ad.AnnData(X=csr_matrix(matrix))
    a.var_names = list(genes)
    a.obs_names = [f"{sid}_{i}" for i in range(a.n_obs)]
    a.obs["cluster"] = ["C1"] * a.n_obs
    a.obsm["spatial"] = np.column_stack([np.arange(a.n_obs), np.arange(a.n_obs) + 5])
    return a


def test_multisample_gene_and_annotation_contract():
    adapter = AnnDataBrowserAdapter({
        "tumor": _sample([[2, 0], [4, 1]], sid="t"),
        "normal": _sample([[0, 1], [1, 2]], sid="n"),
    })
    assert adapter.samples() == ["tumor", "normal"]
    assert adapter.genes() == ["CD8A", "TP53"]
    assert "cluster" in adapter.features()
    view = adapter.view("tumor", "CD8A")
    assert view.values.tolist() == [2, 4]
    assert view.y.tolist() == [5.0, 6.0]
    assert not view.categorical
    assert adapter.view("normal", "cluster").categorical
    summary = adapter.summary("CD8A")
    assert summary[0]["mean_expression"] == 3
    assert summary[1]["detection_fraction"] == 0.5


def test_no_spatial_coordinates_fail_closed():
    a = _sample([[1, 0], [0, 1]])
    del a.obsm["spatial"]
    with pytest.raises(ValueError, match="spatial coordinates"):
        AnnDataBrowserAdapter({"a": a})


def test_split_combined_samples_preserves_local_spot_identity():
    a = _sample([[1, 0], [0, 2]], sid="s")
    a.obs["sample_id"] = ["case", "control"]
    resolved = resolve_browser_samples({"adata": a})
    assert set(resolved) == {"case", "control"}
    assert resolved["case"].n_obs == 1
    assert resolved["control"].n_obs == 1


def test_missing_data_is_empty_not_simulated():
    assert resolve_browser_samples({}) == {}


def test_shared_gene_intersection():
    adapter = AnnDataBrowserAdapter({
        "a": _sample([[1, 2]], genes=("A", "B")),
        "b": _sample([[1, 2]], genes=("B", "C")),
    })
    assert adapter.genes() == ["B"]
