"""Cluster marker discovery for Seurat-like workflow."""

from __future__ import annotations

import anndata as ad
import pandas as pd

from mbsi.analysis.markers import rank_cluster_markers


def find_cluster_markers(
    adata: ad.AnnData,
    groupby: str = "cluster",
    method: str = "wilcoxon",
) -> pd.DataFrame:
    """Find cluster markers; delegates to mbsi.analysis.markers."""
    return rank_cluster_markers(adata, groupby=groupby, method=method)
