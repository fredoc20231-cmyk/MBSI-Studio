"""Differential expression wrappers."""

from __future__ import annotations

from typing import Optional

import anndata as ad
import pandas as pd

from mbsi.statistics.differential import run_cluster_de, run_condition_de
from mbsi.statistics.pseudobulk import run_pseudobulk_de
from mbsi.statistics.replicate_aware import run_replicate_aware_tests


def run_de(
    adata: ad.AnnData,
    *,
    mode: str = "cluster",
    groupby: str = "cluster",
    condition_key: str = "condition",
    test: str = "wilcoxon",
    replicate_key: Optional[str] = "replicate_id",
) -> pd.DataFrame:
    """Unified DE entry point."""
    mode = (mode or "cluster").lower()
    if mode == "cluster" or mode == "domain":
        key = "domain" if mode == "domain" and "domain" in adata.obs else groupby
        return run_cluster_de(adata, groupby=key, test=test)
    if mode == "region":
        key = "tissue_region" if "tissue_region" in adata.obs else groupby
        return run_cluster_de(adata, groupby=key, test=test)
    if mode == "condition":
        if replicate_key and replicate_key in adata.obs.columns:
            result = run_replicate_aware_tests(adata, condition_key=condition_key, replicate_key=replicate_key)
            de = result.get("de_table")
            if isinstance(de, pd.DataFrame) and not de.empty:
                return de
        return run_condition_de(adata, condition_key=condition_key, test=test)
    if mode == "pseudobulk":
        return run_pseudobulk_de(adata, group_key=condition_key)
    return run_cluster_de(adata, groupby=groupby, test=test)
