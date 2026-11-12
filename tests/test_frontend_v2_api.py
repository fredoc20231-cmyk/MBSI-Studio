"""Contract tests for the frontend integration API.

Only synthetic fixtures are used in tests; synthetic data are never served
from the production endpoints.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from anndata import AnnData
from fastapi.testclient import TestClient

from mbsi.api.app import create_app
from mbsi.api import handlers


@pytest.fixture
def api(monkeypatch):
    a = AnnData(X=np.array([[3.0, 1.0], [4, 1], [1, 5], [2, 4]]))
    b = AnnData(X=np.array([[6.0, 1.0], [5, 2], [1, 7], [3, 5]]))
    for obj in (a, b):
        obj.var_names = ["EPCAM", "CD3D"]
        obj.obs["cell_type"] = pd.Categorical(["epithelial", "epithelial", "immune", "immune"])
        obj.obsm["spatial"] = np.array([[0, 0], [1, 1], [8, 1], [9, 2]], dtype=float)
    def _fake_load(dataset_id):
        return (a if dataset_id == "a" else b, []) if dataset_id in ("a", "b") else (None, ["unknown"])
    monkeypatch.setattr(handlers, "_load_adata_for_dataset", _fake_load)
    return TestClient(create_app())


@pytest.mark.unit
def test_frontend_capabilities_are_honest(api):
    data = api.get("/api/v2/capabilities").json()
    assert data["real_data_only"] is True
    assert data["supports"]["visium_hd"] == "adapter_required"
    assert data["supports"]["statistical_inference"] == "not_implemented_in_v2_preview"


@pytest.mark.unit
def test_frontend_dataset_summary_and_genes(api):
    response = api.get("/api/v2/datasets/a/summary")
    assert response.status_code == 200
    assert response.json()["observations"] == 4
    assert response.json()["spatial_available"] is True
    genes = api.get("/api/v2/datasets/a/genes", params={"query": "EPC"}).json()
    assert genes["genes"] == ["EPCAM"]


@pytest.mark.unit
def test_spatial_points_are_bounded_and_real(api):
    response = api.get("/api/v2/datasets/a/spatial-points",
                       params={"annotation": "cell_type", "gene": "EPCAM", "limit": 2})
    assert response.status_code == 200
    assert response.json()["returned_count"] == 2
    assert "expression" in response.json()["points"][0]


@pytest.mark.unit
def test_frontend_comparative_contract(api):
    response = api.post("/api/v2/comparisons/preview", json={
        "reference_dataset_id": "a", "comparison_dataset_id": "b",
        "reference_annotation": "cell_type", "comparison_annotation": "cell_type",
        "genes": ["EPCAM", "CD3D"], "include_similarity": True
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "descriptive_only"
    assert len(data["composition"]) == 2
    assert data["cluster_similarity"]["reference_labels"]
    assert data["provenance"]["inference"] == "none"


@pytest.mark.unit
def test_frontend_rejects_unknown_datasets_and_path_ids(api):
    assert api.get("/api/v2/datasets/unknown/summary").status_code == 404
    assert api.get("/api/v2/datasets/..%2Fsecret/summary").status_code in (404, 422)
    assert api.post("/api/v2/comparisons/preview", json={
        "reference_dataset_id": "a", "comparison_dataset_id": "a",
        "reference_annotation": "cell_type", "comparison_annotation": "cell_type",
        "genes": ["EPCAM"]
    }).status_code == 422


@pytest.mark.unit
def test_visium_qc_contract(api):
    response = api.get("/api/v2/datasets/a/qc")
    assert response.status_code == 200
    data = response.json()
    assert data["n_observations"] == 4
    assert data["matrix_is_integer_counts"] is True
    assert data["detected_features_per_observation"]["median"] == 2


@pytest.mark.unit
def test_roi_real_data_summaries(api):
    response = api.post("/api/v2/datasets/a/roi/summary", json={
        "xmin": -1, "xmax": 2, "ymin": -1, "ymax": 3,
        "annotation": "cell_type", "genes": ["EPCAM", "CD3D"]
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["n_units"] == 2
    assert data["composition"][0]["population"] == "epithelial"
    assert data["expression"][0]["mean_expression"] == pytest.approx(3.5)
    assert api.post("/api/v2/datasets/a/roi/summary", json={
        "xmin": 2, "xmax": 1, "ymin": 1, "ymax": 2,
        "annotation": "cell_type", "genes": ["EPCAM"]
    }).status_code == 422
