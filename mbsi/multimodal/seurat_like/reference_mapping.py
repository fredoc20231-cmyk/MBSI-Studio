"""Reference mapping for query datasets."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import anndata as ad
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


def map_query_to_reference(
    query: ad.AnnData,
    reference: ad.AnnData,
    ref_label_key: str = "cell_type",
    n_neighbors: int = 5,
) -> ad.AnnData:
    """Map query cells to reference labels via kNN in PCA space."""
    query = query.copy()
    if "X_pca" not in query.obsm or "X_pca" not in reference.obsm:
        raise ValueError("Both query and reference need X_pca in obsm")
    if ref_label_key not in reference.obs.columns:
        raise ValueError(f"Reference missing {ref_label_key}")

    knn = KNeighborsClassifier(n_neighbors=min(n_neighbors, reference.n_obs))
    knn.fit(reference.obsm["X_pca"], reference.obs[ref_label_key].astype(str))
    query.obs["predicted_label"] = knn.predict(query.obsm["X_pca"])
    proba = knn.predict_proba(query.obsm["X_pca"])
    query.obs["mapping_confidence"] = proba.max(axis=1)
    return query


def run_reference_mapping(
    query: ad.AnnData,
    reference: ad.AnnData,
    atlas_id: str = "",
    ref_label_key: str = "cell_type",
) -> Dict[str, Any]:
    """Run reference mapping and return results dict."""
    mapped = map_query_to_reference(query, reference, ref_label_key=ref_label_key)
    n_mapped = int((mapped.obs["mapping_confidence"] > 0.5).sum())
    return {
        "adata": mapped,
        "atlas_id": atlas_id,
        "n_mapped": n_mapped,
        "n_query": query.n_obs,
        "label_key": ref_label_key,
        "mean_confidence": float(mapped.obs["mapping_confidence"].mean()),
    }
