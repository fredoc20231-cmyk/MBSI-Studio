"""Tests for spatial domain detection."""

import numpy as np
import pandas as pd
import anndata as ad


def _mini_adata(n=30, g=20):
    X = np.random.poisson(3, (n, g)).astype(float)
    obs = pd.DataFrame(index=[f"spot_{i}" for i in range(n)])
    var = pd.DataFrame(index=[f"G{i}" for i in range(g)])
    adata = ad.AnnData(X, obs=obs, var=var)
    adata.obsm["spatial"] = np.column_stack([np.random.rand(n), np.random.rand(n)])
    return adata


def test_detect_domains():
    from mbsi.domains import detect_domains

    adata = _mini_adata()
    out, summary, warnings = detect_domains(adata, method="leiden", resolution=0.5)
    assert "domain" in out.obs.columns
    assert not summary.empty


def test_domain_to_finding():
    from mbsi.discovery.spatial_workflow_evidence import domain_to_finding

    summary = pd.DataFrame({"domain": ["0", "1"], "n_spots": [15, 15]})
    store, _ = domain_to_finding(summary, "leiden")
    assert len(store.list_findings()) == 1
