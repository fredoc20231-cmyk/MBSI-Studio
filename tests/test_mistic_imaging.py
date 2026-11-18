"""Tests: Mistic-inspired image embedding uses only provided real features."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from mbsi.visualization.mistic_imaging import image_cohort_embedding, image_cohort_layout
from mbsi.api.app import create_app


def test_pca_embedding_and_metadata_are_observed():
    ids = ["fov_01", "fov_02", "fov_03", "fov_04"]
    matrix = np.asarray([[1, 2, 3], [3, 1, 2], [2, 4, 1], [4, 3, 2]])
    out = image_cohort_embedding(ids, matrix, metadata={"fov_02": {"condition": "treated"}})
    assert out.source == "computed_pca_from_observed_features"
    assert len(out.records()) == 4
    assert np.isfinite(out.x).all()
    assert out.records()[1]["condition"] == "treated"


def test_supplied_layout_never_randomizes_points():
    coords = np.asarray([[10, 4], [6, 8]])
    result = image_cohort_layout(["a", "b"], coords)
    assert result.records()[0]["x"] == 10.0
    assert result.records()[1]["y"] == 8.0


def test_reject_invalid_features_and_metadata_overwrite():
    with pytest.raises(ValueError, match="finite"):
        image_cohort_embedding(["a", "b", "c"],
                               np.array([[1, 2], [np.nan, 3], [5, 6]]))
    with pytest.raises(ValueError, match="replace"):
        image_cohort_layout(["a"], [[0, 1]],
                            metadata={"a": {"x": 1000}})


def test_api_imaging_payloads():
    client = TestClient(create_app())
    coords = client.post("/api/v1/imaging/layout", json={
        "image_ids": ["a", "b"], "coordinates": [[1, 2], [3, 4]],
        "metadata": {"a": {"cluster": "immune"}}
    })
    assert coords.status_code == 200
    assert coords.json()["coordinates"][0]["cluster"] == "immune"
    assert coords.json()["coordinates"][1]["x"] == 3.0

    computed = client.post("/api/v1/imaging/embedding", json={
        "image_ids": ["a", "b", "c"],
        "features": [[1, 0], [0, 1], [3, 2]],
        "method": "pca"
    })
    assert computed.status_code == 200
    assert len(computed.json()["coordinates"]) == 3

    bad = client.post("/api/v1/imaging/embedding", json={
        "image_ids": ["a", "b", "c"],
        "features": [[1, 0], [0, 1], [3, 2]],
        "method": "tsne", "perplexity": 50
    })
    assert bad.status_code == 422
