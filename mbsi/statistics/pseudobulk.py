"""Pseudobulk differential expression."""

from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


def run_pseudobulk_de(
    adata: ad.AnnData,
    sample_key: str = "sample_id",
    group_key: str = "condition",
    correction: str = "bh",
) -> pd.DataFrame:
    """Aggregate counts per sample then run DE between groups."""
    if sample_key not in adata.obs.columns or group_key not in adata.obs.columns:
        return pd.DataFrame()

    X = adata.X
    if hasattr(X, "toarray"):
        X = X.toarray()
    samples = adata.obs[sample_key].astype(str)
    groups = adata.obs[group_key].astype(str)
    unique_samples = samples.unique()
    bulk = {}
    sample_group = {}
    for s in unique_samples:
        mask = samples == s
        bulk[s] = X[mask].sum(axis=0)
        sample_group[s] = groups[mask].iloc[0]

    conds = sorted(set(sample_group.values()))
    if len(conds) != 2:
        return pd.DataFrame()
    c1, c2 = conds
    s1 = [s for s, g in sample_group.items() if g == c1]
    s2 = [s for s, g in sample_group.items() if g == c2]
    rows = []
    for gi, gene in enumerate(adata.var_names):
        x1 = np.array([bulk[s][gi] for s in s1], dtype=float)
        x2 = np.array([bulk[s][gi] for s in s2], dtype=float)
        if len(x1) < 1 or len(x2) < 1:
            continue
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
        })
    df = pd.DataFrame(rows)
    if not df.empty and correction == "bh":
        from scipy.stats import false_discovery_control

        df["pval_adj"] = false_discovery_control(df["pval"].values, method="bh")
    return df.sort_values("pval_adj" if "pval_adj" in df.columns else "pval")
