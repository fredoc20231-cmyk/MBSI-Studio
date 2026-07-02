"""Tests for universal ingestion entry point."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from mbsi.io.ingest_universal import IngestionResult, ingest_dataset


def _make_h5ad(path: Path, n_obs=25, n_vars=40) -> Path:
    x = np.random.poisson(4, (n_obs, n_vars)).astype(float)
    adata = ad.AnnData(X=x)
    adata.var_names = [f"g{i}" for i in range(n_vars)]
    adata.obs_names = [f"s{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = np.column_stack([np.random.rand(n_obs), np.random.rand(n_obs)])
    adata.write_h5ad(path)
    return path


def test_ingestion_result_json_serializable():
    result = IngestionResult(
        adata_path="/tmp/x.h5ad",
        platform="visium",
        technology_profile={"key": "visium"},
        readiness={"score": 50},
        compatibility={"qc": {"status": "available"}},
        warnings=["ok"],
        dataset_id="ds1",
    )
    payload = result.to_dict()
    text = json.dumps(payload)
    loaded = json.loads(text)
    assert loaded["platform"] == "visium"
    assert loaded["adata_path"] == "/tmp/x.h5ad"


def test_ingest_h5ad(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    h5ad = _make_h5ad(tmp_path / "sample.h5ad")
    result = ingest_dataset(h5ad, technology_hint="generic_h5ad")
    assert isinstance(result, IngestionResult)
    assert result.platform
    assert result.adata_path
    assert Path(result.adata_path).exists()
    assert result.metadata.get("n_obs") == 25
    assert result.metadata.get("n_vars") == 40
    json.dumps(result.to_dict())


def test_ingest_csv_coords(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    n = 15
    genes = [f"g{i}" for i in range(20)]
    spots = [f"s{i}" for i in range(n)]
    matrix = pd.DataFrame(
        np.random.poisson(2, (n, len(genes))).astype(float),
        index=spots,
        columns=genes,
    )
    coords = pd.DataFrame(
        {"x": np.random.rand(n), "y": np.random.rand(n)},
        index=spots,
    )
    matrix.to_csv(tmp_path / "matrix.csv")
    coords.to_csv(tmp_path / "coordinates.csv")

    result = ingest_dataset(tmp_path / "matrix.csv")
    assert result.adata_path
    assert Path(result.adata_path).exists()
    assert result.platform == "csv_matrix"
    assert result.metadata["n_obs"] == n


def test_ingest_visium_zip_minimal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    n = 10
    genes = [f"g{i}" for i in range(12)]
    spots = [f"AAACCCA-1-{i}" for i in range(n)]
    matrix = pd.DataFrame(
        np.random.poisson(2, (n, len(genes))).astype(float),
        index=spots,
        columns=genes,
    )
    coords = pd.DataFrame(
        {
            "barcode": spots,
            "tissue": [1] * n,
            "row": list(range(n)),
            "col": list(range(n)),
            "imagerow": np.random.rand(n),
            "imagecol": np.random.rand(n),
            "x": np.random.rand(n),
            "y": np.random.rand(n),
        }
    )

    bundle = tmp_path / "visium_bundle"
    spatial = bundle / "spatial"
    spatial.mkdir(parents=True)
    matrix.to_csv(bundle / "matrix.csv")
    coords.to_csv(spatial / "tissue_positions_list.csv")

    zip_path = tmp_path / "visium_sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in bundle.rglob("*"):
            if f.is_file():
                zf.write(f, arcname=str(f.relative_to(bundle.parent)))

    result = ingest_dataset(zip_path, technology_hint="visium")
    assert result.platform == "visium"
    assert isinstance(result.warnings, list)
    # Minimal synthetic bundle may fail full parse — honest error or success both OK
    json.dumps(result.to_dict())


def test_ingest_no_silent_demo_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    missing = tmp_path / "not_a_dataset.txt"
    missing.write_text("hello")
    result = ingest_dataset(missing)
    assert result.adata_path == ""
    assert result.readiness.get("status") in ("unsupported", "error", "stub")
    assert not any("demo" in w.lower() for w in result.warnings)


def test_ingest_readiness_matrix_statuses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from tests.test_visium_ingestion import write_mini_spaceranger

    write_mini_spaceranger(tmp_path / "outs", n_spots=10, n_genes=25)
    result = ingest_dataset(tmp_path / "outs", technology_hint="visium")
    qc = result.compatibility.get("qc_transformation", {})
    viz = result.compatibility.get("visualization", {})
    assert qc.get("status") in ("available", "warn", "unavailable")
    assert viz.get("status") in ("available", "warn", "unavailable")
    assert result.readiness.get("status") in (
        "Missing optional fields",
        "Ready for spatial analysis",
        "Ready for reconstruction",
    )


def test_ingest_stub_platform(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dummy = tmp_path / "merfish_export.txt"
    dummy.write_text("stub")
    result = ingest_dataset(dummy, technology_hint="merfish")
    assert result.platform == "merfish"
    assert result.adata_path == ""
    assert any("stub" in w.lower() or "merfish" in w.lower() for w in result.warnings)
