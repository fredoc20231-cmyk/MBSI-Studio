"""Tests for Visium / Space Ranger ingestion with synthetic mini outs."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import mmwrite
from scipy.sparse import csr_matrix

from mbsi.io.detect import detect_platform
from mbsi.io.visium import load_space_ranger


def _write_mini_spaceranger(root: Path, n_spots: int = 6, n_genes: int = 20) -> None:
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

    rows = []
    for i, bc in enumerate(barcodes):
        rows.append({
            "barcode": bc,
            "in_tissue": 1,
            "array_row": i // 3,
            "array_col": i % 3,
            "pxl_row_in_fullres": float(i * 10),
            "pxl_col_in_fullres": float(i * 12),
        })
    pd.DataFrame(rows).to_csv(spatial / "tissue_positions_list.csv", index=False)
    (spatial / "scalefactors_json.json").write_text(
        json.dumps({"tissue_hires_scalef": 0.5, "tissue_lowres_scalef": 0.1})
    )


def test_detect_mini_visium_dir(tmp_path):
    _write_mini_spaceranger(tmp_path)
    d = detect_platform(tmp_path)
    assert d["platform"] == "visium"
    assert d["confidence"] >= 0.85


def test_load_space_ranger_mini(tmp_path):
    _write_mini_spaceranger(tmp_path, n_spots=8, n_genes=30)
    adata, meta = load_space_ranger(tmp_path)
    assert adata.n_obs == 8
    assert adata.n_vars == 30
    assert "spatial" in adata.obsm
    assert adata.uns["mbsi_platform"] == "visium"
    assert meta["readiness_score"] >= 50
    assert adata.obs["in_tissue"].dtype == bool or adata.obs["in_tissue"].notna().all()


def test_load_space_ranger_zip(tmp_path):
    import shutil
    import zipfile

    outs = tmp_path / "outs"
    _write_mini_spaceranger(outs)
    zip_path = tmp_path / "visium.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in outs.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(tmp_path))
    adata, meta = load_space_ranger(zip_path)
    assert adata.n_obs == 6
    assert meta["platform"] == "visium"
