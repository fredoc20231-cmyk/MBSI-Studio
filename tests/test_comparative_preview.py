"""Comparative preview tests: deterministic, no misleading inferential claims."""
import numpy as np
import pandas as pd
import pytest
from scipy import sparse
from anndata import AnnData

from mbsi.comparative import compare_samples, spatial_coordinates
from mbsi.comparative.neighborhoods import neighborhood_matrix


def make_sample(means=(2, 4), annotations=("T", "T", "B", "B")):
    data = np.array([[means[0], 1], [means[0], 3],
                     [means[1], 1], [means[1], 3]], dtype=float)
    a = AnnData(X=sparse.csr_matrix(data))
    a.var_names = ["CD3D", "MS4A1"]
    a.obs["cell_type"] = pd.Categorical(annotations)
    a.obsm["spatial"] = np.array([[0, 0], [1, 0], [9, 0], [10, 0]], dtype=float)
    return a


@pytest.mark.unit
def test_descriptive_cross_sample_result():
    a, b = make_sample(), make_sample(means=(3, 8))
    result = compare_samples(a, b, left_id="pre", right_id="post")
    assert result["status"] == "descriptive"
    assert result["composition"]["fraction_a"].sum() == pytest.approx(1)
    assert result["composition"]["fraction_b"].sum() == pytest.approx(1)
    row = result["expression"].query("population == 'T' and gene == 'CD3D'").iloc[0]
    assert row["delta_mean"] == pytest.approx(1)
    assert not any("p_value" in x for x in result["expression"].columns)
    assert len(result["warnings"]) > 0


@pytest.mark.unit
def test_unmatched_labels_not_falsely_corresponded():
    a = make_sample()
    b = make_sample(annotations=("Other", "Other", "B", "B"))
    result = compare_samples(a, b)
    assert set(result["composition"]["population"]) == {"T", "B", "Other"}
    assert set(result["expression"]["population"]) == {"B"}


@pytest.mark.unit
def test_no_shared_genes_rejected():
    a, b = make_sample(), make_sample()
    b.var_names = ["OTHER1", "OTHER2"]
    with pytest.raises(ValueError, match="common gene"):
        compare_samples(a, b)


@pytest.mark.unit
def test_neighborhood_matrix_is_valid():
    a = make_sample()
    table = neighborhood_matrix(a, "cell_type", k=1)
    assert set(table.index) == {"T", "B"}
    assert np.allclose(table.sum(axis=1), 1.0)
    assert spatial_coordinates(a).shape == (4, 2)


@pytest.mark.unit
def test_missing_spatial_coordinates_rejected():
    a = make_sample()
    del a.obsm["spatial"]
    with pytest.raises(ValueError, match="coordinates"):
        neighborhood_matrix(a, "cell_type")


@pytest.mark.unit
def test_no_missing_count_layers_silently_selected():
    with pytest.raises(ValueError, match="Layer"):
        compare_samples(make_sample(), make_sample(), layer="counts")
