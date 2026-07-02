"""Xenium ingestion tests — synthetic bundle structure for Milestone 1."""

from __future__ import annotations

import gzip
import json
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from mbsi.io.detect import detect_platform
from mbsi.io.ingest_universal import ingest_dataset
from mbsi.io.xenium import load_xenium


def write_mini_xenium_bundle(root: Path, n_cells: int = 12, n_genes: int = 25) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    X = csr_matrix(rng.poisson(4, (n_genes, n_cells)).astype(float))
    cell_ids = [f"cell_{i:04d}" for i in range(n_cells)]
    genes = [f"GENE{i}" for i in range(n_genes)]

    h5_path = root / "cell_feature_matrix.h5"
    with h5py.File(h5_path, "w") as f:
        grp = f.create_group("matrix")
        csc = X.tocsc()
        grp.create_dataset("data", data=csc.data)
        grp.create_dataset("indices", data=csc.indices)
        grp.create_dataset("indptr", data=csc.indptr)
        grp.create_dataset("shape", data=np.array([n_genes, n_cells]))
        grp.create_dataset("barcodes", data=np.array(cell_ids, dtype="S"))
        feat = grp.create_group("features")
        feat.create_dataset("name", data=np.array(genes, dtype="S"))

    rows = []
    for i, cid in enumerate(cell_ids):
        rows.append(
            {
                "cell_id": cid,
                "x_centroid": float(i * 8.5),
                "y_centroid": float(i * 6.2),
                "transcript_counts": int(X[:, i].sum()),
            }
        )
    cells_csv = pd.DataFrame(rows).to_csv(index=False)
    with gzip.open(root / "cells.csv.gz", "wt") as handle:
        handle.write(cells_csv)

    (root / "experiment.xenium").write_text(json.dumps({"format": "synthetic"}))


def test_xenium_detection(tmp_path):
    write_mini_xenium_bundle(tmp_path)
    detection = detect_platform(tmp_path)
    assert detection["platform"] == "xenium"
    assert detection["confidence"] >= 0.9
    assert "full_xenium_loader_phase2" not in detection.get("missing", [])


def test_load_xenium_bundle(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=15, n_genes=40)
    adata, meta = load_xenium(tmp_path)
    assert adata.n_obs == 15
    assert adata.n_vars == 40
    assert "spatial" in adata.obsm
    assert adata.obsm["spatial"].shape == (15, 2)
    assert "x_centroid" in adata.obs.columns
    assert "y_centroid" in adata.obs.columns
    assert adata.uns["mbsi_platform"] == "xenium"
    assert meta["readiness_score"] >= 50
    assert "xenium" in adata.uns


def test_xenium_ingest_universal_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_mini_xenium_bundle(tmp_path / "xenium_outs", n_cells=10, n_genes=30)
    result = ingest_dataset(tmp_path / "xenium_outs", technology_hint="xenium")
    assert result.platform == "xenium"
    assert result.adata_path
    assert Path(result.adata_path).exists()
    assert result.metadata["n_obs"] == 10
    assert result.readiness.get("status") in (
        "Missing optional fields",
        "Ready for spatial analysis",
        "Ready for reconstruction",
    )


def test_xenium_cells_parquet(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=8, n_genes=20)
    import gzip

    with gzip.open(tmp_path / "cells.csv.gz", "rt") as handle:
        cells = pd.read_csv(handle)
    (tmp_path / "cells.csv.gz").unlink()
    cells.to_parquet(tmp_path / "cells.parquet")
    adata, meta = load_xenium(tmp_path)
    assert adata.n_obs == 8
    assert "x_centroid" in adata.obs.columns
    assert meta["platform"] == "xenium"


def test_xenium_ingest_universal_zip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = tmp_path / "xenium_run"
    write_mini_xenium_bundle(bundle)
    zip_path = tmp_path / "xenium_sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in bundle.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(tmp_path))
    result = ingest_dataset(zip_path, technology_hint="xenium")
    assert result.platform == "xenium"
    assert result.adata_path
    assert Path(result.adata_path).exists()
    assert result.metadata["n_obs"] == 12
    assert result.compatibility.get("visualization", {}).get("status") in ("available", "warn")
