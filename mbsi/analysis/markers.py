"""Cluster marker gene analysis."""

from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from mbsi.utils import to_dense_array


def _expression_matrix(adata: ad.AnnData, layer: str = "logcounts") -> np.ndarray:
    if layer in adata.layers:
        X = adata.layers[layer]
    else:
        X = adata.X
    return to_dense_array(X)


def rank_cluster_markers(adata: ad.AnnData, groupby: str = "cluster", method: str = "wilcoxon") -> pd.DataFrame:
    """Rank markers per cluster; return long dataframe."""
    if groupby not in adata.obs.columns:
        raise ValueError(f"Column {groupby} not in adata.obs")

    X = _expression_matrix(adata)
    groups = adata.obs[groupby].astype(str)
    cluster_ids = sorted(groups.unique())
    rows = []
    for cluster in cluster_ids:
        in_grp = groups == cluster
        out_grp = ~in_grp
        if in_grp.sum() < 2 or out_grp.sum() < 2:
            continue
        for gi, gene in enumerate(adata.var_names):
            x_in = X[in_grp, gi]
            x_out = X[out_grp, gi]
            try:
                stat, pval = mannwhitneyu(x_in, x_out, alternative="two-sided")
            except ValueError:
                continue
            mean_in = float(x_in.mean())
            mean_out = float(x_out.mean()) + 1e-12
            lfc = float(np.log2((mean_in + 1e-12) / mean_out))
            rows.append({
                "cluster": cluster,
                "gene": gene,
                "score": float(stat),
                "logfoldchange": lfc,
                "pval": float(pval),
                "pval_adj": float(pval),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        from scipy.stats import false_discovery_control

        df["pval_adj"] = false_discovery_control(df["pval"].values, method="bh")
        df = df.sort_values(["cluster", "pval_adj", "score"], ascending=[True, True, False])
    return df


def top_markers_per_cluster(marker_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N markers per cluster by score."""
    if marker_df.empty:
        return marker_df
    return (
        marker_df.sort_values(["cluster", "score"], ascending=[True, False])
        .groupby("cluster", as_index=False)
        .head(n)
    )


def marker_expression_matrix(
    adata: ad.AnnData,
    genes: list,
    groupby: str = "cluster",
    layer: str = "logcounts",
) -> pd.DataFrame:
    """Return group-level average expression matrix."""
    genes = [g for g in genes if g in adata.var_names]
    if not genes or groupby not in adata.obs.columns:
        return pd.DataFrame()

    X = _expression_matrix(adata, layer=layer)
    gene_idx = [list(adata.var_names).index(g) for g in genes]
    groups = adata.obs[groupby].astype(str)
    mat = []
    for g in sorted(groups.unique()):
        mask = (groups == g).values
        mat.append(X[mask][:, gene_idx].mean(axis=0))
    return pd.DataFrame(
        np.array(mat),
        index=sorted(groups.unique()),
        columns=genes,
    )
