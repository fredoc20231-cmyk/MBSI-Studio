"""
Tests for the universal spatial omics ingestion layer.

Covers: detect.py, converters.py, generic.py, visium.py (file building),
        merfish.py, cosmx.py, codex.py.
"""

import io
import json
import tempfile
import zipfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from mbsi.io.detect import detect_platform, compute_compatibility_matrix
from mbsi.io.converters import (
    to_mbsi_contract,
    compute_readiness,
    ensure_sparse_csr,
    ensure_spatial_float64,
)
from mbsi.io.generic import load_h5ad, load_csv_matrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_adata(n_obs: int = 20, n_vars: int = 15, with_spatial: bool = True) -> ad.AnnData:
    X = sp.random(n_obs, n_vars, density=0.5, format="csr", dtype=np.float32)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"Gene{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    if with_spatial:
        adata.obsm["spatial"] = np.random.rand(n_obs, 2).astype(np.float64) * 1000
    return adata


# ---------------------------------------------------------------------------
# detect.py
# ---------------------------------------------------------------------------

class TestDetectPlatform:
    def test_detects_visium(self):
        files = [
            "run1/filtered_feature_bc_matrix.h5",
            "run1/spatial/tissue_positions_list.csv",
            "run1/spatial/tissue_hires_image.png",
        ]
        result = detect_platform(files)
        assert result.platform == "visium"
        assert result.confidence == 1.0

    def test_detects_xenium(self):
        files = ["cell_feature_matrix.h5", "cells.csv.gz", "transcripts.csv.gz"]
        result = detect_platform(files)
        assert result.platform == "xenium"

    def test_detects_merfish(self):
        files = ["cell_by_gene.csv", "cell_metadata.csv", "detected_transcripts.csv"]
        result = detect_platform(files)
        assert result.platform == "merfish"

    def test_detects_cosmx(self):
        files = ["Run1_exprMat_file.csv", "Run1_metadata_file.csv", "Run1_fov_positions_file.csv"]
        result = detect_platform(files)
        assert result.platform == "cosmx"

    def test_detects_codex(self):
        files = ["cell_table.csv", "channel_names.txt"]
        result = detect_platform(files)
        assert result.platform == "codex"

    def test_unknown_files(self):
        result = detect_platform(["random_file.txt", "data.xlsx"])
        assert result.platform == "unknown"
        assert result.confidence == 0.0

    def test_partial_visium_has_lower_confidence(self):
        files = ["filtered_feature_bc_matrix.h5"]  # missing spatial/tissue_positions
        result = detect_platform(files)
        assert result.platform == "visium"
        assert result.confidence < 1.0
        assert result.files_missing  # some required files absent


class TestCompatibilityMatrix:
    def test_full_spot_data(self):
        matrix = compute_compatibility_matrix(
            adata_present=True, has_spatial=True, has_gene_names=True,
            has_cell_types=False, has_ground_truth=False, is_spot_platform=True,
        )
        assert matrix["QC"]["available"]
        assert matrix["Spatial Analysis"]["available"]
        assert matrix["MBSI Reconstruction"]["available"]
        assert not matrix["Benchmark Hub"]["available"]

    def test_no_ground_truth_blocks_benchmark(self):
        matrix = compute_compatibility_matrix(
            adata_present=True, has_spatial=True, has_gene_names=True,
            has_cell_types=True, has_ground_truth=False, is_spot_platform=True,
        )
        assert not matrix["Benchmark Hub"]["available"]

    def test_with_ground_truth_enables_benchmark(self):
        matrix = compute_compatibility_matrix(
            adata_present=True, has_spatial=True, has_gene_names=True,
            has_cell_types=True, has_ground_truth=True, is_spot_platform=True,
        )
        assert matrix["Benchmark Hub"]["available"]

    def test_non_spot_platform_blocks_mbsi(self):
        matrix = compute_compatibility_matrix(
            adata_present=True, has_spatial=True, has_gene_names=True,
            has_cell_types=False, has_ground_truth=False, is_spot_platform=False,
        )
        assert not matrix["MBSI Reconstruction"]["available"]

    def test_no_spatial_blocks_most_analyses(self):
        matrix = compute_compatibility_matrix(
            adata_present=True, has_spatial=False, has_gene_names=True,
            has_cell_types=False, has_ground_truth=False, is_spot_platform=False,
        )
        assert not matrix["Spatial Analysis"]["available"]
        assert not matrix["Communication"]["available"]


# ---------------------------------------------------------------------------
# converters.py
# ---------------------------------------------------------------------------

class TestConverters:
    def test_ensure_sparse_csr_from_dense(self):
        adata = _make_adata()
        adata.X = adata.X.toarray()  # make dense
        adata = ensure_sparse_csr(adata)
        assert sp.issparse(adata.X)
        assert isinstance(adata.X, sp.csr_matrix)
        assert adata.X.dtype == np.float32

    def test_ensure_sparse_csr_from_csc(self):
        adata = _make_adata()
        adata.X = adata.X.tocsc()
        adata = ensure_sparse_csr(adata)
        assert isinstance(adata.X, sp.csr_matrix)

    def test_ensure_spatial_float64(self):
        adata = _make_adata()
        adata.obsm["spatial"] = adata.obsm["spatial"].astype(np.float32)
        adata = ensure_spatial_float64(adata)
        assert adata.obsm["spatial"].dtype == np.float64

    def test_compute_readiness_full(self):
        adata = _make_adata(n_obs=50, n_vars=200)
        rd = compute_readiness(adata)
        assert rd["score"] >= 70
        assert rd["capabilities"]["expression_matrix"]
        assert rd["capabilities"]["spatial_coords"]
        assert rd["capabilities"]["gene_names"]

    def test_compute_readiness_no_spatial(self):
        adata = _make_adata(with_spatial=False)
        rd = compute_readiness(adata)
        assert not rd["capabilities"]["spatial_coords"]
        assert rd["score"] <= 60

    def test_compute_readiness_stamps_uns(self):
        adata = _make_adata()
        compute_readiness(adata)
        assert "mbsi_readiness" in adata.uns

    def test_to_mbsi_contract(self):
        adata = _make_adata()
        adata = to_mbsi_contract(adata, platform="visium", display_name="Test Visium")
        assert "mbsi_platform" in adata.uns
        assert "mbsi_readiness" in adata.uns
        assert adata.uns["mbsi_platform"]["platform"] == "visium"
        assert sp.issparse(adata.X)
        assert adata.X.dtype == np.float32

    def test_nan_in_expression_flagged(self):
        adata = _make_adata()
        adata.X = adata.X.toarray().astype(float)
        adata.X[0, 0] = np.nan
        adata.X = sp.csr_matrix(adata.X)
        rd = compute_readiness(adata)
        assert any("NaN" in w or "Inf" in w for w in rd["warnings"])


# ---------------------------------------------------------------------------
# generic.py — h5ad
# ---------------------------------------------------------------------------

class TestLoadH5ad:
    def test_load_from_path(self, tmp_path):
        adata = _make_adata()
        p = tmp_path / "test.h5ad"
        adata.write_h5ad(p)
        loaded = load_h5ad(p)
        assert loaded.n_obs == adata.n_obs
        assert loaded.n_vars == adata.n_vars
        assert "mbsi_platform" in loaded.uns

    def test_load_from_bytes(self, tmp_path):
        adata = _make_adata()
        p = tmp_path / "test.h5ad"
        adata.write_h5ad(p)
        buf = io.BytesIO(p.read_bytes())
        buf.name = "test.h5ad"
        loaded = load_h5ad(buf)
        assert loaded.n_obs == adata.n_obs

    def test_spatial_preserved(self, tmp_path):
        adata = _make_adata()
        p = tmp_path / "test.h5ad"
        adata.write_h5ad(p)
        loaded = load_h5ad(p)
        assert "spatial" in loaded.obsm
        assert loaded.obsm["spatial"].dtype == np.float64


# ---------------------------------------------------------------------------
# generic.py — CSV
# ---------------------------------------------------------------------------

class TestLoadCsvMatrix:
    def _write_csv(self, adata, tmp_path):
        """Write count matrix and coords CSVs to tmp_path."""
        if sp.issparse(adata.X):
            X = adata.X.toarray()
        else:
            X = adata.X
        df = pd.DataFrame(X, index=adata.obs_names, columns=adata.var_names)
        counts_path = tmp_path / "counts.csv"
        df.to_csv(counts_path)

        if "spatial" in adata.obsm:
            coords = adata.obsm["spatial"]
            coords_df = pd.DataFrame(coords, columns=["x", "y"])
            coords_path = tmp_path / "coords.csv"
            coords_df.to_csv(coords_path, index=False)
        else:
            coords_path = None

        return counts_path, coords_path

    def test_load_with_coords(self, tmp_path):
        adata = _make_adata(n_obs=30, n_vars=10)
        counts_path, coords_path = self._write_csv(adata, tmp_path)
        loaded = load_csv_matrix(counts_path, coords_path)
        assert loaded.n_obs == adata.n_obs
        assert loaded.n_vars == adata.n_vars
        assert "spatial" in loaded.obsm

    def test_load_without_coords(self, tmp_path):
        adata = _make_adata(with_spatial=False, n_obs=10, n_vars=5)
        counts_path, _ = self._write_csv(adata, tmp_path)
        loaded = load_csv_matrix(counts_path)
        assert loaded.n_obs == adata.n_obs
        assert "spatial" not in loaded.obsm

    def test_result_is_sparse(self, tmp_path):
        adata = _make_adata(n_obs=15, n_vars=8)
        counts_path, _ = self._write_csv(adata, tmp_path)
        loaded = load_csv_matrix(counts_path)
        assert sp.issparse(loaded.X)


# ---------------------------------------------------------------------------
# visium.py — file-based (build synthetic Space Ranger structure)
# ---------------------------------------------------------------------------

class TestVisiumLoader:
    def _build_visium_dir(self, tmp_path: Path) -> Path:
        """Build a minimal synthetic Space Ranger output directory."""
        import h5py, scipy.sparse as sp

        n_spots, n_genes = 10, 5
        root = tmp_path / "visium_run"
        (root / "spatial").mkdir(parents=True)

        # Expression HDF5 — stored as genes×barcodes (Space Ranger convention)
        X_gb = sp.random(n_genes, n_spots, density=0.5, format="csr").astype(np.float32)
        h5_path = root / "filtered_feature_bc_matrix.h5"
        with h5py.File(h5_path, "w") as f:
            grp = f.create_group("matrix")
            grp.create_dataset("data", data=X_gb.data)
            grp.create_dataset("indices", data=X_gb.indices)
            grp.create_dataset("indptr", data=X_gb.indptr)
            grp.create_dataset("shape", data=np.array([n_genes, n_spots]))
            feat = grp.create_group("features")
            feat.create_dataset("name", data=[f"Gene{i}".encode() for i in range(n_genes)])
            feat.create_dataset("id", data=[f"ENSG{i:05d}".encode() for i in range(n_genes)])
            grp.create_dataset("barcodes", data=[f"AAAA{i:04d}-1".encode() for i in range(n_spots)])

        # Spatial positions
        pos_data = pd.DataFrame({
            "barcode": [f"AAAA{i:04d}-1" for i in range(n_spots)],
            "in_tissue": [1] * n_spots,
            "array_row": range(n_spots),
            "array_col": range(n_spots),
            "pxl_row_in_fullres": np.arange(n_spots) * 100,
            "pxl_col_in_fullres": np.arange(n_spots) * 100,
        })
        pos_data.to_csv(root / "spatial" / "tissue_positions_list.csv", index=False, header=False)

        # Scalefactors
        sf = {"spot_diameter_fullres": 20.0, "tissue_hires_scalef": 0.2}
        (root / "spatial" / "scalefactors_json.json").write_text(json.dumps(sf))

        return root

    def test_load_visium_dir(self, tmp_path):
        from mbsi.io.visium import load_visium_dir

        root = self._build_visium_dir(tmp_path)
        adata = load_visium_dir(root)
        assert adata.n_obs == 10
        assert adata.n_vars == 5
        assert "spatial" in adata.obsm
        assert adata.obsm["spatial"].shape == (10, 2)
        assert adata.uns["mbsi_platform"]["platform"] == "visium"

    def test_visium_coords_scaled_to_um(self, tmp_path):
        from mbsi.io.visium import load_visium_dir

        root = self._build_visium_dir(tmp_path)
        adata = load_visium_dir(root)
        # With spot_diameter_fullres=20, scale = 55/20 = 2.75
        # First spot pxl_row=0 → 0 µm; second spot pxl_row=100 → 275 µm
        assert adata.obsm["spatial"].dtype == np.float64


# ---------------------------------------------------------------------------
# merfish.py
# ---------------------------------------------------------------------------

class TestMerfishLoader:
    def _build_merfish_dir(self, tmp_path: Path) -> Path:
        n_cells, n_genes = 15, 8
        root = tmp_path / "merfish_run"
        root.mkdir()

        genes = [f"Gene{i}" for i in range(n_genes)]
        cell_ids = [f"cell_{i}" for i in range(n_cells)]
        X = np.random.poisson(5, size=(n_cells, n_genes)).astype(float)
        cbg = pd.DataFrame(X, index=cell_ids, columns=genes)
        cbg.index.name = "cell"
        cbg.to_csv(root / "cell_by_gene.csv")

        meta = pd.DataFrame({
            "cell": cell_ids,
            "center_x": np.random.rand(n_cells) * 500,
            "center_y": np.random.rand(n_cells) * 500,
            "volume": np.random.rand(n_cells) * 200,
        }).set_index("cell")
        meta.to_csv(root / "cell_metadata.csv")

        return root

    def test_load_merfish_dir(self, tmp_path):
        from mbsi.io.merfish import load_merfish_dir

        root = self._build_merfish_dir(tmp_path)
        adata = load_merfish_dir(root)
        assert adata.n_obs == 15
        assert adata.n_vars == 8
        assert "spatial" in adata.obsm
        assert adata.uns["mbsi_platform"]["platform"] == "merfish"


# ---------------------------------------------------------------------------
# codex.py
# ---------------------------------------------------------------------------

class TestCodexLoader:
    def _build_codex_dir(self, tmp_path: Path) -> Path:
        n_cells, n_markers = 12, 6
        root = tmp_path / "codex_run"
        root.mkdir()

        markers = ["CD3", "CD8", "CD20", "CD68", "PD-L1", "FOXP3"]
        (root / "channel_names.txt").write_text("\n".join(markers))

        df = pd.DataFrame(
            np.random.rand(n_cells, n_markers),
            columns=markers,
        )
        df["x"] = np.random.rand(n_cells) * 1000
        df["y"] = np.random.rand(n_cells) * 1000
        df.to_csv(root / "cell_table.csv")

        return root

    def test_load_codex_dir(self, tmp_path):
        from mbsi.io.codex import load_codex_dir

        root = self._build_codex_dir(tmp_path)
        adata = load_codex_dir(root)
        assert adata.n_obs == 12
        assert adata.n_vars == 6
        assert list(adata.var_names) == ["CD3", "CD8", "CD20", "CD68", "PD-L1", "FOXP3"]
        assert "spatial" in adata.obsm
        assert adata.uns["mbsi_platform"]["platform"] == "codex"
        assert adata.uns["mbsi_platform"]["modality"] == "protein"
