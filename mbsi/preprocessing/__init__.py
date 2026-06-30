"""Normalization wrappers — delegates to seurat_like."""

from __future__ import annotations

from typing import Tuple

import anndata as ad

from mbsi.analysis.seurat_like.normalization import normalize_log1p, run_sctransform_like


def normalize(
    adata: ad.AnnData,
    method: str = "log",
    target_sum: float = 1e4,
) -> Tuple[ad.AnnData, str]:
    """Normalize AnnData. Methods: log, sctransform_like, clr, tfidf_lsi, none."""
    method = (method or "log").lower().replace(" ", "_")
    adata = adata.copy()
    note = ""

    if method in ("none", "skip"):
        return adata, "No normalization applied."

    if method in ("log", "log1p", "log_normalize"):
        adata = normalize_log1p(adata, target_sum=target_sum)
        adata.layers["logcounts"] = adata.X.copy()
        return adata, "Log-normalized (target_sum=1e4)."

    if method in ("sctransform", "sctransform_like", "sct"):
        adata, note = run_sctransform_like(adata)
        adata.layers["logcounts"] = adata.X.copy()
        return adata, note or "SCTransform-like normalization."

    if method == "clr":
        import numpy as np

        X = adata.X
        if hasattr(X, "toarray"):
            X = X.toarray()
        X = np.asarray(X, dtype=float)
        geom = np.exp(np.mean(np.log(X + 1), axis=1, keepdims=True))
        adata.X = np.log1p(X / (geom + 1e-12))
        adata.layers["logcounts"] = adata.X.copy()
        return adata, "CLR normalization (CODEX/protein-style)."

    if method in ("tfidf", "tfidf_lsi", "atac"):
        import numpy as np

        X = adata.X
        if hasattr(X, "toarray"):
            X = X.toarray()
        X = np.asarray(X, dtype=float)
        tf = X / (X.sum(axis=1, keepdims=True) + 1e-12)
        idf = np.log1p(X.shape[0] / (X > 0).sum(axis=0, keepdims=True))
        adata.X = tf * idf
        adata.layers["logcounts"] = adata.X.copy()
        return adata, "TF-IDF normalization (Spatial ATAC-style; LSI in reduction step)."

    adata = normalize_log1p(adata, target_sum=target_sum)
    adata.layers["logcounts"] = adata.X.copy()
    return adata, f"Unknown method '{method}' — fell back to log normalization."
