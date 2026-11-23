"""Contract tests for Lovable's observed-data spatial explorer."""
import json
from uuid import uuid4

import anndata as ad
import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.sparse import csr_matrix

from mbsi.api.app import create_app


@pytest.fixture
def client_with_spatial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ds = str(uuid4())
    root = tmp_path / "data" / "registry"
    (root / "datasets").mkdir(parents=True)
    ingested = root / "ingested" / ds
    ingested.mkdir(parents=True)
    a = ad.AnnData(X=csr_matrix([[2, 0], [0, 3], [4, 5]]))
    a.obs_names = ["spot1", "spot2", "spot3"]
    a.var_names = ["CD8A", "TP53"]
    a.obs["cluster"] = ["immune", "tumor", "immune"]
    a.obsm["spatial"] = np.asarray([[10., 20.], [30., 40.], [50., 60.]])
    file_path = ingested / "dataset.h5ad"
    a.write_h5ad(file_path)
    (root / "datasets" / f"{ds}.json").write_text(json.dumps({
        "dataset_id": ds, "project_id": "p1", "sample_id": "sample1",
        "platform": "visium", "adata_path": str(file_path),
        "metadata": {"n_obs": 3, "n_vars": 2},
        "readiness": {"status": "ready"},
    }))
    return TestClient(create_app()), ds


def test_dataset_listing_filters_and_hides_server_paths(client_with_spatial):
    client, ds = client_with_spatial
    response = client.get("/api/v1/datasets?project_id=p1")
    assert response.status_code == 200
    records = response.json()["datasets"]
    assert len(records) == 1 and records[0]["dataset_id"] == ds
    assert "adata_path" not in records[0]
    assert client.get("/api/v1/datasets?project_id=other").json()["datasets"] == []


def test_gene_search_and_real_spatial_values(client_with_spatial):
    client, ds = client_with_spatial
    features = client.get(f"/api/v1/datasets/{ds}/features?query=CD8").json()
    assert features["genes"] == ["CD8A"]
    assert features["annotations"] == ["cluster"]
    response = client.get(f"/api/v1/datasets/{ds}/spatial?gene=CD8A")
    assert response.status_code == 200
    points = response.json()["points"]
    assert [p["value"] for p in points] == [2., 0., 4.]
    assert [p["x"] for p in points] == [10., 30., 50.]
    assert response.json()["downsampled"] is False


def test_annotations_and_bounded_sampling(client_with_spatial):
    client, ds = client_with_spatial
    response = client.get(f"/api/v1/datasets/{ds}/spatial?annotation=cluster&limit=2")
    assert response.status_code == 200
    assert response.json()["downsampled"] is True
    assert response.json()["returned_observations"] == 2
    assert response.json()["points"][0]["value"] == "immune"


def test_bad_input_rejected(client_with_spatial):
    client, ds = client_with_spatial
    assert client.get(f"/api/v1/datasets/{ds}/spatial").status_code == 422
    assert client.get(f"/api/v1/datasets/{ds}/spatial?gene=CD8A&annotation=cluster").status_code == 422
    assert client.get(f"/api/v1/datasets/{ds}/spatial?gene=missing").status_code == 404
    assert client.get("/api/v1/datasets/..%2F..%2Fsecrets/features").status_code in (404, 422)


def test_exact_polygon_selection_and_statistics(client_with_spatial):
    client, ds = client_with_spatial
    # Rectangle includes spots 1 and 2 but excludes spot 3.
    polygon = [[0, 10], [40, 10], [40, 50], [0, 50]]
    response = client.post(
        f"/api/v1/datasets/{ds}/selection",
        json={"gene": "CD8A", "polygon": polygon, "threshold": 1.0},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["selected_observations"] == 2
    assert payload["barcodes"] == ["spot1", "spot2"]
    assert payload["barcodes_truncated"] is False
    assert payload["statistics"]["mean"] == 1.0
    assert payload["statistics"]["fraction_detected"] == 0.5
    assert payload["statistics"]["above_threshold"] == 1
    assert payload["inference"] is False


def test_exact_polygon_annotation_boundary_and_empty_roi(client_with_spatial):
    client, ds = client_with_spatial
    polygon = [[10, 20], [30, 20], [30, 40], [10, 40]]
    response = client.post(
        f"/api/v1/datasets/{ds}/selection",
        json={"annotation": "cluster", "polygon": polygon},
    )
    assert response.status_code == 200, response.text
    assert response.json()["statistics"]["category_counts"] == {"immune": 1, "tumor": 1}
    empty = client.post(
        f"/api/v1/datasets/{ds}/selection",
        json={"gene": "TP53", "polygon": [[100, 100], [101, 100], [100, 101]]},
    )
    assert empty.status_code == 200
    assert empty.json()["selected_observations"] == 0
    assert empty.json()["statistics"]["mean"] is None


def test_exact_polygon_rejects_invalid_input(client_with_spatial):
    client, ds = client_with_spatial
    zero_area = [[0, 0], [1, 1], [2, 2]]
    response = client.post(
        f"/api/v1/datasets/{ds}/selection", json={"gene": "CD8A", "polygon": zero_area}
    )
    assert response.status_code == 422
    polygon = [[0, 0], [40, 0], [40, 50], [0, 50]]
    assert client.post(f"/api/v1/datasets/{ds}/selection",
                       json={"gene": "CD8A", "annotation": "cluster", "polygon": polygon}).status_code == 422
    assert client.post(f"/api/v1/datasets/{ds}/selection",
                       json={"gene": "MISSING", "polygon": polygon}).status_code == 404
    assert client.post(f"/api/v1/datasets/{ds}/selection",
                       json={"annotation": "cluster", "threshold": 1, "polygon": polygon}).status_code == 422
