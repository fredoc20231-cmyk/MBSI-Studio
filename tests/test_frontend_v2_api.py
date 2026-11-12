"""Tests for Lovable-ready API without optional HTTP client dependencies."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from anndata import AnnData
from fastapi import HTTPException

from mbsi.api.app import create_app
from mbsi.api import handlers
from mbsi.api.frontend_v2 import (
    capabilities, dataset_summary, dataset_genes, dataset_qc,
    spatial_points, comparison_preview, roi_preview,
    ComparisonRequest, ROIRequest
)


@pytest.fixture
def samples(monkeypatch):
    a = AnnData(X=np.array([[3.0, 1.0], [4, 1], [1, 5], [2, 4]]))
    b = AnnData(X=np.array([[6.0, 1.0], [5, 2], [1, 7], [3, 5]]))
    for obj in (a, b):
        obj.var_names = ["EPCAM", "CD3D"]
        obj.obs["cell_type"] = pd.Categorical(["epithelial", "epithelial", "immune", "immune"])
        obj.obsm["spatial"] = np.array([[0, 0], [1, 1], [8, 1], [9, 2]], dtype=float)
    def fake_load(dataset_id):
        return (a if dataset_id == "a" else b, []) if dataset_id in ("a", "b") else (None, ["unknown"])
    monkeypatch.setattr(handlers, "_load_adata_for_dataset", fake_load)
    return a, b


@pytest.mark.unit
def test_v2_routes_in_app():
    paths = {route.path for route in create_app().routes if hasattr(route, 'path')}
    assert "/api/v2/capabilities" in paths
    assert "/api/v2/datasets/{dataset_id}/summary" in paths
    assert "/api/v2/datasets/{dataset_id}/roi/summary" in paths
    assert "/api/v2/comparisons/preview" in paths


@pytest.mark.unit
def test_frontend_capabilities_are_honest():
    data = capabilities()
    assert data["real_data_only"] is True
    assert data["supports"]["visium_hd"] == "adapter_required"
    assert data["supports"]["statistical_inference"] == "not_implemented_in_v2_preview"


@pytest.mark.unit
def test_frontend_dataset_summary_and_genes(samples):
    data = dataset_summary("a")
    assert data["observations"] == 4
    assert data["spatial_available"] is True
    genes = dataset_genes("a", query="EPC", limit=20)
    assert genes["genes"] == ["EPCAM"]


@pytest.mark.unit
def test_spatial_points_bounded_real_data(samples):
    response = spatial_points("a", annotation="cell_type", gene="EPCAM", limit=2)
    assert response["returned_count"] == 2
    assert "expression" in response["points"][0]


@pytest.mark.unit
def test_frontend_comparative_contract(samples):
    data = comparison_preview(ComparisonRequest(
        reference_dataset_id="a", comparison_dataset_id="b",
        reference_annotation="cell_type", comparison_annotation="cell_type",
        genes=["EPCAM", "CD3D"], include_similarity=True
    ))
    assert data["status"] == "descriptive_only"
    assert len(data["composition"]) == 2
    assert data["cluster_similarity"]["reference_labels"]
    assert data["provenance"]["inference"] == "none"


@pytest.mark.unit
def test_reject_unknown_datasets_and_path_ids(samples):
    with pytest.raises(HTTPException) as exc:
        dataset_summary("unknown")
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException) as exc:
        dataset_summary("../secret")
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        comparison_preview(ComparisonRequest(
            reference_dataset_id="a", comparison_dataset_id="a",
            reference_annotation="cell_type", comparison_annotation="cell_type",
            genes=["EPCAM"]
        ))
    assert exc.value.status_code == 422


@pytest.mark.unit
def test_visium_qc_contract(samples):
    data = dataset_qc("a")
    assert data["n_observations"] == 4
    assert data["matrix_is_integer_counts"] is True
    assert data["detected_features_per_observation"]["median"] == 2


@pytest.mark.unit
def test_roi_real_data_summaries(samples):
    data = roi_preview("a", ROIRequest(
        xmin=-1, xmax=2, ymin=-1, ymax=3,
        annotation="cell_type", genes=["EPCAM", "CD3D"]
    ))
    assert data["n_units"] == 2
    assert data["composition"][0]["population"] == "epithelial"
    assert data["expression"][0]["mean_expression"] == pytest.approx(3.5)
    with pytest.raises(HTTPException) as exc:
        roi_preview("a", ROIRequest(
            xmin=2, xmax=1, ymin=1, ymax=2,
            annotation="cell_type", genes=["EPCAM"]
        ))
    assert exc.value.status_code == 422
