"""Differential expression statistics."""

from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def _expr(adata: ad.AnnData) -> np.ndarray:
    X = adata.layers.get("logcounts", adata.X)
    return np.asarray(X.toarray() if hasattr(X, "toarray") else X, dtype=float)


def run_cluster_de(
    adata: ad.AnnData,
    groupby: str = "cluster",
    test: str = "wilcoxon",
    correction: str = "bh",
) -> pd.DataFrame:
    """DE between clusters."""
    from mbsi.analysis.seurat_like.differential_expression import run_differential_expression

    return run_differential_expression(adata, groupby=groupby, test=test, correction=correction)


def run_condition_de(
    adata: ad.AnnData,
    condition_key: str = "condition",
    test: str = "wilcoxon",
    correction: str = "bh",
) -> pd.DataFrame:
    """DE between conditions."""
    if condition_key not in adata.obs.columns:
        return pd.DataFrame()
    conditions = adata.obs[condition_key].astype(str).unique()
    if len(conditions) != 2:
        return pd.DataFrame()
    c1, c2 = conditions[:2]
    m1 = adata.obs[condition_key].astype(str) == c1
    m2 = adata.obs[condition_key].astype(str) == c2
    X = _expr(adata)
    rows = []
    for gi, gene in enumerate(adata.var_names):
        x1, x2 = X[m1, gi], X[m2, gi]
        try:
            stat, pval = mannwhitneyu(x1, x2, alternative="two-sided")
        except ValueError:
            continue
        rows.append({
            "gene": gene,
            "group1": c1,
            "group2": c2,
            "logfoldchange": float(np.log2((x1.mean() + 1e-12) / (x2.mean() + 1e-12))),
            "pval": float(pval),
            "score": float(stat),
            "test": test,
        })
    df = pd.DataFrame(rows)
    if not df.empty and correction == "bh":
        from scipy.stats import false_discovery_control

        df["pval_adj"] = false_discovery_control(df["pval"].values, method="bh")
    return df.sort_values("pval_adj" if "pval_adj" in df.columns else "pval")
