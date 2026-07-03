"""End-to-end tests for the vendor-format spatial-omics loaders.

Builds minimal but realistic synthetic bundles for MERSCOPE/MERFISH, CosMx,
CODEX and spatial-ATAC, then loads each through both the direct loader and the
universal ``ingest_dataset`` dispatcher, asserting the MBSI AnnData contract.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mbsi.io.merfish import load_merfish
from mbsi.io.cosmx import load_cosmx
from mbsi.io.codex import load_codex
from mbsi.io.spatial_atac import load_spatial_atac
from mbsi.io.ingest_universal import ingest_dataset
from mbsi.io.validators import validate_adata_contract

rng = np.random.default_rng(0)
N_CELLS, N_GENES = 60, 30


def _genes(n=N_GENES):
    return [f"Gene{i:03d}" for i in range(n)]


# ---------------------------------------------------------------- MERFISH ----
def _make_merscope(root: Path):
    genes = _genes() + ["Blank-1", "Blank-2"]
    ids = [f"cell_{i}" for i in range(N_CELLS)]
    counts = pd.DataFrame(rng.poisson(3, size=(N_CELLS, len(genes))), index=ids, columns=genes)
    counts.index.name = "cell"
    counts.to_csv(root / "cell_by_gene.csv")
    meta = pd.DataFrame(
        {"center_x": rng.uniform(0, 1000, N_CELLS), "center_y": rng.uniform(0, 1000, N_CELLS),
         "volume": rng.uniform(50, 200, N_CELLS)}, index=ids)
    meta.index.name = "cell"
    meta.to_csv(root / "cell_metadata.csv")


def test_merfish_loader(tmp_path):
    _make_merscope(tmp_path)
    adata, meta = load_merfish(tmp_path)
    assert adata.n_obs == N_CELLS and adata.n_vars == N_GENES + 2
    assert adata.obsm["spatial"].shape == (N_CELLS, 2)
    assert meta["platform"] == "merfish"
    assert adata.var["control_probe"].sum() == 2
    assert validate_adata_contract(adata)["valid"]


def test_merfish_via_dispatcher(tmp_path):
    _make_merscope(tmp_path)
    res = ingest_dataset(tmp_path, technology_hint="merfish")
    assert res.platform == "merfish"
    assert res.metadata["n_obs"] == N_CELLS
    assert res.readiness.get("score", 0) >= 70


# ------------------------------------------------------------------ CosMx ----
def _make_cosmx(root: Path):
    genes = _genes() + ["NegPrb1", "NegPrb2"]
    rows = []
    metas = []
    for fov in (1, 2):
        for cid in range(0, N_CELLS // 2 + 1):  # cid 0 = background
            row = {"fov": fov, "cell_ID": cid}
            for g in genes:
                row[g] = rng.poisson(2)
            rows.append(row)
            metas.append({"fov": fov, "cell_ID": cid,
                          "CenterX_global_px": rng.uniform(0, 5000),
                          "CenterY_global_px": rng.uniform(0, 5000),
                          "Area": rng.uniform(100, 400)})
    pd.DataFrame(rows).to_csv(root / "run_exprMat_file.csv", index=False)
    pd.DataFrame(metas).to_csv(root / "run_metadata_file.csv", index=False)


def test_cosmx_loader(tmp_path):
    _make_cosmx(tmp_path)
    adata, meta = load_cosmx(tmp_path)
    # background cells (cell_ID 0) dropped: 2 fov * (N/2) real cells
    assert adata.n_obs == 2 * (N_CELLS // 2)
    assert adata.n_vars == N_GENES + 2
    assert meta["platform"] == "cosmx"
    assert adata.var["control_probe"].sum() == 2
    assert "fov" in adata.obs
    assert validate_adata_contract(adata)["valid"]


def test_cosmx_via_dispatcher(tmp_path):
    _make_cosmx(tmp_path)
    res = ingest_dataset(tmp_path, technology_hint="cosmx")
    assert res.platform == "cosmx"
    assert res.metadata["n_obs"] == 2 * (N_CELLS // 2)


# ------------------------------------------------------------------ CODEX ----
def _make_codex(root: Path):
    markers = ["CD3", "CD8", "CD20", "PanCK", "Ki67", "DAPI"]
    df = pd.DataFrame({m: rng.uniform(0, 255, N_CELLS) for m in markers})
    df["cell_id"] = [f"c{i}" for i in range(N_CELLS)]
    df["x"] = rng.uniform(0, 2000, N_CELLS)
    df["y"] = rng.uniform(0, 2000, N_CELLS)
    df["area"] = rng.uniform(50, 300, N_CELLS)
    df["region"] = rng.integers(0, 3, N_CELLS)
    df.to_csv(root / "cell_data.csv", index=False)


def test_codex_loader(tmp_path):
    _make_codex(tmp_path)
    adata, meta = load_codex(tmp_path)
    assert adata.n_obs == N_CELLS
    # DAPI is metadata → excluded; 5 real markers remain
    assert set(adata.var_names) == {"CD3", "CD8", "CD20", "PanCK", "Ki67"}
    assert meta["platform"] == "codex"
    assert adata.uns["codex"]["modality"] == "protein_intensity"
    assert validate_adata_contract(adata)["valid"]


def test_codex_via_dispatcher(tmp_path):
    _make_codex(tmp_path)
    res = ingest_dataset(tmp_path, technology_hint="codex")
    assert res.platform == "codex"
    assert res.metadata["n_vars"] == 5


# ------------------------------------------------------------ spatial ATAC ----
def _make_atac(root: Path):
    from scipy.sparse import random as sprand
    from scipy.io import mmwrite
    n_feat = 40
    peaks = [f"chr1:{i*1000}-{i*1000+500}" for i in range(n_feat)]
    barcodes = [f"BC{i:04d}-1" for i in range(N_CELLS)]
    X = (sprand(n_feat, N_CELLS, density=0.3, random_state=0) * 10).tocsr()
    X.data = np.ceil(X.data)
    mmwrite(str(root / "matrix.mtx"), X)  # features x cells (MTX convention)
    (root / "peaks.bed").write_text("\n".join(peaks) + "\n")
    (root / "barcodes.tsv").write_text("\n".join(barcodes) + "\n")
    # Visium-style header-less positions: barcode,in_tissue,row,col,pxl_row,pxl_col
    pos_rows = [f"{bc},1,{i},{i},{rng.uniform(0,3000):.1f},{rng.uniform(0,3000):.1f}"
                for i, bc in enumerate(barcodes)]
    (root / "tissue_positions_list.csv").write_text("\n".join(pos_rows) + "\n")


def test_spatial_atac_loader(tmp_path):
    _make_atac(tmp_path)
    adata, meta = load_spatial_atac(tmp_path)
    assert adata.n_obs == N_CELLS
    assert adata.n_vars == 40
    assert meta["platform"] == "spatial_atac"
    assert adata.uns["spatial_atac"]["feature_type"] == "peaks"
    assert validate_adata_contract(adata)["valid"]


def test_spatial_atac_via_dispatcher(tmp_path):
    _make_atac(tmp_path)
    res = ingest_dataset(tmp_path, technology_hint="spatial_atac")
    assert res.platform == "spatial_atac"
    assert res.metadata["n_obs"] == N_CELLS
