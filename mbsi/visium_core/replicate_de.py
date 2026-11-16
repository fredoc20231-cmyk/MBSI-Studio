"""Phase 4 — replicate-aware pseudobulk DE (sample x domain) with anti-pseudoreplication guard."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from .provenance import BlockedAnalysis, require
from .spatial import bh_fdr


def replicate_check(design: pd.DataFrame, condition_key: str, min_reps: int = 2) -> Dict[str, int]:
    reps = design.groupby(condition_key)["sample"].nunique().to_dict()
    short = {k: v for k, v in reps.items() if v < min_reps}
    if len(reps) < 2:
        raise BlockedAnalysis("Differential testing needs at least two conditions.", "Assign samples to two or more conditions.")
    if short:
        raise BlockedAnalysis(
            f"Blocked: fewer than {min_reps} biological replicates per condition {short}. Spot-level tests would be pseudoreplication.",
            f"Provide at least {min_reps} independent samples per condition.",
        )
    return {str(k): int(v) for k, v in reps.items()}


def pseudobulk(adata, sample_key: str, group_key: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    X = adata.layers["counts"] if "counts" in adata.layers else adata.X
    keys = adata.obs[sample_key].astype(str) + "|" + adata.obs[group_key].astype(str)
    rows, meta = [], []
    for k in keys.unique():
        m = (keys == k).to_numpy()
        rows.append(np.asarray(X[m].sum(axis=0)).ravel())
        s, g = k.split("|", 1)
        meta.append({"pb_id": k, "sample": s, "domain": g, "n_spots": int(m.sum())})
    counts = pd.DataFrame(np.vstack(rows), index=[r["pb_id"] for r in meta], columns=adata.var_names)
    return counts.round().astype(int), pd.DataFrame(meta).set_index("pb_id")


def replicate_aware_de(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sample_key = params.get("sample_key", "sample")
    cond_key = params.get("condition_key", "condition")
    domain_key = params.get("domain_key", "spatial_niche")
    for k in (sample_key, cond_key, domain_key):
        if k not in adata.obs:
            raise BlockedAnalysis(f"Observation column '{k}' is missing.", "Merge samples with sample, condition and domain labels.")
    counts, meta = pseudobulk(adata, sample_key, domain_key)
    cond_map = adata.obs.groupby(sample_key, observed=True)[cond_key].first().astype(str)
    meta["condition"] = meta["sample"].map(cond_map)
    reps = replicate_check(meta.rename(columns={}).reset_index(), "condition", int(params.get("min_replicates", 2)))
    dds_mod = require("pydeseq2.dds", "Install pydeseq2.")
    ds_mod = require("pydeseq2.ds", "Install pydeseq2.")
    ref, test = params.get("reference"), params.get("test")
    levels = sorted(meta["condition"].unique())
    ref = ref or levels[0]
    test = test or levels[1]
    results = []
    for dom in sorted(meta["domain"].unique()):
        sel = meta["domain"] == dom
        sub = meta[sel]
        if sub.groupby("condition")["sample"].nunique().min() < 2:
            results.append({"domain": dom, "status": "blocked", "reason": "fewer than 2 replicates in this domain"})
            continue
        dds = dds_mod.DeseqDataSet(counts=counts[sel], metadata=sub[["condition"]], design="~condition", quiet=True)
        dds.deseq2()
        st = ds_mod.DeseqStats(dds, contrast=["condition", test, ref], quiet=True)
        st.summary()
        df = st.results_df.dropna(subset=["pvalue"]).copy()
        df["padj_bh"] = bh_fdr(df["pvalue"].to_numpy())
        top = df.sort_values("padj_bh").head(100).reset_index(names="gene")
        results.append({"domain": dom, "status": "complete", "n_significant": int((df["padj_bh"] < 0.05).sum()), "top_genes": top.round(6).to_dict(orient="records")})
    return {"contrast": f"{test} vs {ref}", "replicates_per_condition": reps, "unit": "pseudobulk sample x domain", "domains": results}
