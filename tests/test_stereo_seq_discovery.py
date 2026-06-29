"""Tests for Stereo-seq discovery finding functions."""

import anndata as ad
import numpy as np

from mbsi.discovery.stereo_discovery import (
    identify_micro_niches,
    identify_spatial_gradients,
    identify_transition_boundaries,
    identify_ultra_local_signaling,
    identify_ultra_resolution_biomarkers,
    run_stereo_seq_discovery,
)
from mbsi.discovery_model.entities import Finding


def _stereo_adata(n=80, n_genes=50):
    X = np.random.poisson(4, (n, n_genes)).astype(float)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"G{i}" for i in range(n_genes)]
    adata.obs_names = [f"b{i}" for i in range(n)]
    adata.obsm["spatial"] = np.column_stack([np.random.rand(n), np.random.rand(n)])
    adata.obs["cluster"] = np.random.choice(["A", "B", "C"], n)
    adata.obs["stereo_scale"] = "bin"
    adata.uns["mbsi_platform"] = "stereo_seq"
    return adata


def test_identify_micro_niches_returns_findings():
    adata = _stereo_adata()
    findings = identify_micro_niches(adata)
    assert findings
    assert all(isinstance(f, Finding) for f in findings)
    assert findings[0].platform == "stereo_seq"


def test_identify_transition_boundaries():
    findings = identify_transition_boundaries(_stereo_adata())
    assert isinstance(findings, list)


def test_identify_spatial_gradients():
    findings = identify_spatial_gradients(_stereo_adata())
    assert all(isinstance(f, Finding) for f in findings)


def test_identify_ultra_resolution_biomarkers():
    findings = identify_ultra_resolution_biomarkers(_stereo_adata())
    assert len(findings) == 5
    assert findings[0].finding_type == "biomarker"


def test_run_stereo_seq_discovery_bundle():
    out = run_stereo_seq_discovery(_stereo_adata())
    assert out["n_findings"] >= 1
    assert all(isinstance(f, Finding) for f in out["findings"])


def test_gated_on_non_stereo_platform():
    adata = _stereo_adata()
    adata.uns["mbsi_platform"] = "visium"
    try:
        identify_micro_niches(adata)
        raised = False
    except ValueError:
        raised = True
    assert raised
