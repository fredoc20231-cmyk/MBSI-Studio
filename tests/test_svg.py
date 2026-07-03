"""Tests for mbsi.analysis.svg (spatially variable gene detection)."""

import anndata as ad
import numpy as np
import pytest

from mbsi.analysis import spatial_stats as ss
from mbsi.analysis import svg


def _synthetic_adata(seed=0, side=18):
    rng = np.random.default_rng(seed)
    n = side * side
    xx, yy = np.meshgrid(np.arange(side), np.arange(side))
    coords = np.c_[xx.ravel(), yy.ravel()].astype(float)
    grad = coords[:, 0] + 0.1 * rng.standard_normal(n)
    blob = np.exp(-((coords[:, 0] - side / 2) ** 2 + (coords[:, 1] - side / 2) ** 2) / 8.0)
    blob = blob + 0.05 * rng.standard_normal(n)
    noise = rng.standard_normal((n, 2))
    X = np.c_[grad, blob, noise].astype(np.float32)
    A = ad.AnnData(X=X)
    A.var_names = ["grad", "blob", "noise1", "noise2"]
    A.obsm["spatial"] = coords
    A.layers["logcounts"] = X
    return A


def test_vectorized_matches_reference():
    """Vectorized Moran/Geary must equal the per-gene reference implementation."""
    A = _synthetic_adata()
    W = ss.build_spatial_weights(A, k=6)
    X = np.asarray(A.layers["logcounts"], dtype=float)
    I_vec = svg.morans_i_vectorized(X, W)
    C_vec = svg.gearys_c_vectorized(X, W)
    ref_I = ss.morans_i(A, list(A.var_names), k=6)["morans_i"].values
    ref_C = ss.gearys_c(A, list(A.var_names), k=6)["gearys_c"].values
    assert np.allclose(I_vec, ref_I, atol=1e-7)
    assert np.allclose(C_vec, ref_C, atol=1e-7)


def test_moran_geary_relationship():
    """High Moran's I genes should have low Geary's C and vice-versa."""
    A = _synthetic_adata()
    W = ss.build_spatial_weights(A, k=6)
    X = np.asarray(A.layers["logcounts"], dtype=float)
    I = svg.morans_i_vectorized(X, W)
    C = svg.gearys_c_vectorized(X, W)
    # structured genes (idx 0,1) vs noise (idx 2,3)
    assert I[0] > 0.5 and I[1] > 0.5
    assert I[2] < 0.2 and I[3] < 0.2
    assert C[0] < 0.5 and C[1] < 0.5
    assert C[2] > 0.7 and C[3] > 0.7


def test_detect_calls_structured_genes():
    A = _synthetic_adata()
    res = svg.detect_svgs(A, genes=list(A.var_names), n_perms=199,
                          fdr_alpha=0.05, n_top=None, random_state=1)
    called = set(res.loc[res["is_svg"], "gene"])
    assert {"grad", "blob"}.issubset(called)
    assert "noise1" not in called and "noise2" not in called


def test_fdr_monotone_and_bounded():
    p = np.array([0.001, 0.01, 0.02, 0.2, 0.5, 0.9])
    q = svg.benjamini_hochberg(p)
    assert np.all(q >= 0) and np.all(q <= 1)
    # q-values are monotone in p when p is sorted
    order = np.argsort(p)
    assert np.all(np.diff(q[order]) >= -1e-12)
    # q >= p always for BH
    assert np.all(q + 1e-12 >= p)


def test_null_calibration():
    """Pure-noise genes: raw permutation p-values ~ uniform; ~5% below 0.05."""
    rng = np.random.default_rng(3)
    side = 16
    n = side * side
    xx, yy = np.meshgrid(np.arange(side), np.arange(side))
    coords = np.c_[xx.ravel(), yy.ravel()].astype(float)
    Xn = rng.standard_normal((n, 200)).astype(np.float32)
    A = ad.AnnData(X=Xn)
    A.obsm["spatial"] = coords
    A.layers["logcounts"] = Xn
    A.var_names = [f"n{i}" for i in range(200)]
    res = svg.detect_svgs(A, genes=list(A.var_names), n_perms=299,
                          fdr_alpha=0.05, n_top=None, random_state=4)
    fp = (res["pval"] < 0.05).mean()
    assert fp < 0.15, f"false-positive rate too high: {fp}"
    assert res["is_svg"].mean() < 0.05


def test_geary_method_runs():
    A = _synthetic_adata()
    res = svg.detect_svgs(A, genes=list(A.var_names), method="geary",
                          n_perms=199, n_top=None, random_state=1)
    assert "gearys_c" in res.columns
    called = set(res.loc[res["is_svg"], "gene"])
    assert {"grad", "blob"}.issubset(called)


def test_requires_spatial():
    A = ad.AnnData(X=np.random.rand(10, 3).astype(np.float32))
    with pytest.raises(ValueError):
        svg.detect_svgs(A)


def test_zero_variance_gene_handled():
    A = _synthetic_adata()
    # force a constant gene
    X = A.layers["logcounts"].copy()
    X[:, 3] = 1.0
    A.layers["logcounts"] = X
    A.X = X
    res = svg.detect_svgs(A, genes=list(A.var_names), n_perms=99,
                          n_top=None, random_state=1)
    row = res.loc[res["gene"] == "noise2"].iloc[0]
    assert np.isnan(row["morans_i"])
    assert not row["is_svg"]
