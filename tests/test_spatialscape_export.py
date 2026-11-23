"""Offline SpatialScape interoperability and safe registry contract tests."""
import json

import anndata as ad
import numpy as np
import pytest

from scripts.export_spatialscape_bundle import prepare_config


@pytest.fixture
def observed_registry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry = tmp_path / "data" / "registry"
    source_dir = registry / "ingested" / "dataset1"
    source_dir.mkdir(parents=True)
    (registry / "datasets").mkdir(parents=True)
    a = ad.AnnData(X=np.array([[1., 2.], [3., 0.]]))
    a.var_names = ["GENE1", "GENE2"]
    a.obs["cluster"] = ["immune", "tumor"]
    a.obs["patient_name"] = ["Sensitive", "Sensitive"]
    a.obsm["spatial"] = np.array([[10., 20.], [30., 40.]])
    source = source_dir / "dataset.h5ad"
    a.write_h5ad(source)
    (registry / "datasets" / "dataset1.json").write_text(json.dumps({
        "adata_path": str(source), "platform": "xenium", "sample_id": "slide_A",
    }))
    return registry


def test_builds_minimal_safe_config_with_explicit_units(observed_registry):
    cfg = prepare_config(
        observed_registry, ["dataset1"], "test_atlas", "Observed atlas",
        already_microns=True,
    )
    assert cfg["samples"][0]["coords"] == "obsm/spatial"
    assert cfg["samples"][0]["platform"] == "xenium"
    assert cfg["samples"][0]["microns"] == {"already_microns": True}
    assert cfg["samples"][0]["fields"] == {"cluster": "cluster"}
    assert "patient_name" not in cfg["samples"][0]["fields"]


def test_requires_coordinate_scale(observed_registry):
    with pytest.raises(ValueError, match="exactly one"):
        prepare_config(observed_registry, ["dataset1"], "atlas", "Atlas")
    with pytest.raises(ValueError, match="positive"):
        prepare_config(observed_registry, ["dataset1"], "atlas", "Atlas", microns_per_unit=0)


def test_rejects_unowned_adata_path(observed_registry, tmp_path):
    outside = tmp_path / "outside.h5ad"
    outside.write_bytes(b"not-a-matrix")
    record = observed_registry / "datasets" / "dataset1.json"
    payload = json.loads(record.read_text())
    payload["adata_path"] = str(outside)
    record.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="server-ingested"):
        prepare_config(observed_registry, ["dataset1"], "atlas", "Atlas", already_microns=True)
