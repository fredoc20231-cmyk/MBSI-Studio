"""Tests for mbsi.io.loaders module (18% -> target ~50%)."""

import os
import tempfile

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.loaders import load_counts_and_coords, load_h5ad, load_image


def _make_h5ad(path, n_obs=20, n_vars=10, seed=0):
    rng = np.random.RandomState(seed)
    adata = ad.AnnData(X=rng.rand(n_obs, n_vars).astype(np.float32))
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = rng.rand(n_obs, 2).astype(np.float32)
    adata.write_h5ad(path)
    return adata


def test_load_h5ad():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.h5ad")
        original = _make_h5ad(path)
        loaded = load_h5ad(path)
        assert loaded.n_obs == original.n_obs
        assert loaded.n_vars == original.n_vars


def test_load_counts_and_coords_csv():
    with tempfile.TemporaryDirectory() as tmpdir:
        n_obs, n_vars = 15, 8
        rng = np.random.RandomState(42)

        counts = pd.DataFrame(
            rng.rand(n_obs, n_vars),
            index=[f"cell_{i}" for i in range(n_obs)],
            columns=[f"gene_{i}" for i in range(n_vars)],
        )
        coords = pd.DataFrame(
            {"x": rng.rand(n_obs), "y": rng.rand(n_obs)},
        )

        counts_path = os.path.join(tmpdir, "counts.csv")
        coords_path = os.path.join(tmpdir, "coords.csv")
        counts.to_csv(counts_path)
        coords.to_csv(coords_path, index=False)

        adata = load_counts_and_coords(counts_path, coords_path, counts_format="csv")
        assert adata.n_obs == n_obs
        assert adata.n_vars == n_vars
        assert "spatial" in adata.obsm


def test_load_counts_and_coords_tsv():
    with tempfile.TemporaryDirectory() as tmpdir:
        n_obs, n_vars = 10, 5
        rng = np.random.RandomState(0)

        counts = pd.DataFrame(
            rng.rand(n_obs, n_vars),
            index=[f"cell_{i}" for i in range(n_obs)],
            columns=[f"gene_{i}" for i in range(n_vars)],
        )
        coords = pd.DataFrame({"x": rng.rand(n_obs), "y": rng.rand(n_obs)})

        counts_path = os.path.join(tmpdir, "counts.tsv")
        coords_path = os.path.join(tmpdir, "coords.csv")
        counts.to_csv(counts_path, sep="\t")
        coords.to_csv(coords_path, index=False)

        adata = load_counts_and_coords(counts_path, coords_path, counts_format="tsv")
        assert adata.n_obs == n_obs


def test_load_counts_and_coords_invalid_format():
    import pytest

    with tempfile.TemporaryDirectory() as tmpdir:
        counts_path = os.path.join(tmpdir, "c.csv")
        coords_path = os.path.join(tmpdir, "x.csv")
        pd.DataFrame({"a": [1]}).to_csv(counts_path)
        pd.DataFrame({"x": [1], "y": [2]}).to_csv(coords_path, index=False)
        with pytest.raises(ValueError, match="Unknown counts format"):
            load_counts_and_coords(counts_path, coords_path, counts_format="parquet")


def test_load_image():
    from PIL import Image

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "test.png")
        img = Image.fromarray(np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8))
        img.save(img_path)
        loaded = load_image(img_path)
        assert loaded.shape == (32, 32, 3)
