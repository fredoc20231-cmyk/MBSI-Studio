"""Tests for replicate-aware statistics."""

import pandas as pd

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.statistics.replicate_aware import run_replicate_aware_tests


def test_replicate_aware_pseudobulk():
    adata = make_synthetic_visium_adata(n_spots=24, n_genes=60, seed=5)
    adata.obs["sample_id"] = [f"s{i // 6}" for i in range(24)]
    adata.obs["condition"] = ["ctrl"] * 12 + ["treat"] * 12
    adata.obs["replicate_id"] = [str(i // 6) for i in range(24)]
    meta = pd.DataFrame({
        "sample_id": [f"s{i}" for i in range(4)],
        "condition": ["ctrl", "ctrl", "treat", "treat"],
        "replicate_id": ["1", "2", "1", "2"],
    })
    out = run_replicate_aware_tests(adata, sample_metadata=meta)
    assert out["method"] in ("pseudobulk", "spot_level")
    assert "de_results" in out
