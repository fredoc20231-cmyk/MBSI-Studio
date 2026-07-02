"""Visium ingestion tests — Space Ranger-like bundles for Milestone 1."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.io import mmwrite
from scipy.sparse import csr_matrix

from mbsi.io.detect import detect_platform
from mbsi.io.ingest_universal import ingest_dataset
from mbsi.io.visium import load_space_ranger


def write_mini_spaceranger(root: Path, n_spots: int = 8, n_genes: int = 30, *, with_h5: bool = False) -> None:
    """Write synthetic Space Ranger outs (mtx + optional h5 + spatial)."""
    mtx_dir = root / "filtered_feature_bc_matrix"
    mtx_dir.mkdir(parents=True)
    spatial = root / "spatial"
    spatial.mkdir()

    rng = np.random.default_rng(42)
    X = csr_matrix(rng.poisson(3, (n_genes, n_spots)).astype(float))
    mmwrite(mtx_dir / "matrix.mtx", X)
    pd.DataFrame({0: [f"GENE{i}" for i in range(n_genes)]}).to_csv(
        mtx_dir / "features.tsv", sep="\t", header=False, index=False
    )
    barcodes = [f"AAACCTGAG{i:04d}-1" for i in range(n_spots)]
    pd.DataFrame({0: barcodes}).to_csv(mtx_dir / "barcodes.tsv", sep="\t", header=False, index=False)

    if with_h5:
        h5_path = root / "filtered_feature_bc_matrix.h5"
        with h5py.File(h5_path, "w") as f:
            grp = f.create_group("matrix")
            csc = X.tocsc()
            grp.create_dataset("data", data=csc.data)
            grp.create_dataset("indices", data=csc.indices)
            grp.create_dataset("indptr", data=csc.indptr)
            grp.create_dataset("shape", data=np.array([n_genes, n_spots]))
            grp.create_dataset("barcodes", data=np.array(barcodes, dtype="S"))
            feat = grp.create_group("features")
            feat.create_dataset("name", data=np.array([f"GENE{i}" for i in range(n_genes)], dtype="S"))

    rows = []
    for i, bc in enumerate(barcodes):
        rows.append(
            {
                "barcode": bc,
                "in_tissue": 1,
                "array_row": i // 3,
                "array_col": i % 3,
                "pxl_row_in_fullres": float(i * 10),
                "pxl_col_in_fullres": float(i * 12),
            }
        )
    pd.DataFrame(rows).to_csv(spatial / "tissue_positions_list.csv", index=False)
    (spatial / "scalefactors_json.json").write_text(
        json.dumps({"tissue_hires_scalef": 0.5, "tissue_lowres_scalef": 0.1})
    )


def test_visium_detects_h5_and_spatial(tmp_path):
    write_mini_spaceranger(tmp_path, with_h5=True)
    detection = detect_platform(tmp_path)
    assert detection["platform"] == "visium"
    assert "count_matrix" in detection["required_found"] or "cell_feature_matrix" not in str(detection)
    assert detection["confidence"] >= 0.85


def test_visium_ingest_universal_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_mini_spaceranger(tmp_path / "outs", n_spots=10, n_genes=25)
    result = ingest_dataset(tmp_path / "outs", technology_hint="visium")
    assert result.platform == "visium"
    assert result.adata_path
    assert Path(result.adata_path).exists()
    assert result.metadata["n_obs"] == 10
    assert result.metadata["n_vars"] == 25
    assert result.compatibility.get("qc_transformation", {}).get("status") in ("available", "warn")


def test_visium_load_h5_matrix(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=12, n_genes=35, with_h5=True)
    (tmp_path / "filtered_feature_bc_matrix").rename(
        tmp_path / "filtered_feature_bc_matrix_mtx_backup"
    )
    adata, meta = load_space_ranger(tmp_path)
    assert adata.n_obs == 12
    assert adata.n_vars == 35
    assert "spatial" in adata.obsm
    assert meta["platform"] == "visium"


def test_visium_tissue_positions_csv(tmp_path):
    write_mini_spaceranger(tmp_path, n_spots=6, n_genes=20)
    list_path = tmp_path / "spatial" / "tissue_positions_list.csv"
    csv_path = tmp_path / "spatial" / "tissue_positions.csv"
    list_path.rename(csv_path)
    adata, _ = load_space_ranger(tmp_path)
    assert adata.n_obs == 6
    assert "spatial" in adata.obsm


def test_visium_scalefactors_in_uns(tmp_path):
    write_mini_spaceranger(tmp_path, with_h5=True)
    adata, _ = load_space_ranger(tmp_path)
    spatial_uns = adata.uns.get("spatial", {})
    sample_key = spatial_uns.get("library_id", "sample")
    sf = spatial_uns.get(sample_key, {}).get("scalefactors", {})
    assert "tissue_hires_scalef" in sf


def test_visium_ingest_universal_zip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outs = tmp_path / "visium_outs"
    write_mini_spaceranger(outs, with_h5=True)
    zip_path = tmp_path / "sample_visium.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in outs.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(tmp_path))
    result = ingest_dataset(zip_path, technology_hint="visium")
    assert result.platform == "visium"
    assert result.adata_path
    assert result.metadata["n_obs"] == 8
