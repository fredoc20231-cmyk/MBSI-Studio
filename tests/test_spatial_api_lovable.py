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
