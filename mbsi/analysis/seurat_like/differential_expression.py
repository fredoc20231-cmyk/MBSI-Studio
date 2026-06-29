"""Differential expression for Seurat-like workflow."""

from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def _expression_matrix(adata: ad.AnnData, layer: str = "logcounts") -> np.ndarray:
    if layer in adata.layers:
        X = adata.layers[layer]
    else:
        X = adata.X
    return np.asarray(X.toarray() if hasattr(X, "toarray") else X, dtype=float)


def run_differential_expression(
    adata: ad.AnnData,
    groupby: str = "cluster",
    test: str = "wilcoxon",
    correction: str = "bh",
) -> pd.DataFrame:
    """Run DE between groups; returns long dataframe with pval_adj."""
    if groupby not in adata.obs.columns:
        return pd.DataFrame()

    X = _expression_matrix(adata)
    groups = adata.obs[groupby].astype(str)
    cluster_ids = sorted(groups.unique())
    rows = []
    for i, g1 in enumerate(cluster_ids):
        for g2 in cluster_ids[i + 1 :]:
            m1 = groups == g1
            m2 = groups == g2
            if m1.sum() < 2 or m2.sum() < 2:
                continue
            for gi, gene in enumerate(adata.var_names):
                x1 = X[m1, gi]
                x2 = X[m2, gi]
                try:
                    stat, pval = mannwhitneyu(x1, x2, alternative="two-sided")
                except ValueError:
                    continue
                lfc = float(np.log2((x1.mean() + 1e-12) / (x2.mean() + 1e-12)))
                rows.append({
                    "group1": g1,
                    "group2": g2,
                    "gene": gene,
                    "logfoldchange": lfc,
                    "pval": float(pval),
                    "score": float(stat),
                    "test": test,
                })
    df = pd.DataFrame(rows)
    if not df.empty and correction == "bh":
        from scipy.stats import false_discovery_control

        df["pval_adj"] = false_discovery_control(df["pval"].values, method="bh")
        df = df.sort_values("pval_adj")
    return df
