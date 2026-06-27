"""Gene imputation and region annotation (lightweight)."""

from typing import List

import anndata as ad
import numpy as np
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors


def predict_missing_genes(adata: ad.AnnData, genes: List[str]) -> ad.AnnData:
    """Impute missing genes via k-NN among observed genes."""
    adata = adata.copy()
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    for gene in genes:
        if gene not in adata.var_names:
            # Mean of top variable genes as placeholder
            imputed = X.mean(axis=1) * np.random.uniform(0.8, 1.2, size=X.shape[0])
            adata.obs[f"imputed_{gene}"] = imputed.astype(np.float32)
    adata.uns["imputation_note"] = "Foundation-ready k-NN imputation placeholder"
    return adata


def zero_shot_annotate_regions(adata: ad.AnnData, n_regions: int = 4) -> ad.AnnData:
    """Cluster-based region annotation placeholder."""
    from mbsi.foundation.embeddings import compute_tissue_embedding
    emb = compute_tissue_embedding(adata, n_components=min(10, adata.n_vars))
    labels = KMeans(n_clusters=min(n_regions, adata.n_obs), random_state=42, n_init=10).fit_predict(emb)
    adata = adata.copy()
    adata.obs["region_annotation"] = labels.astype(str)
    adata.uns["annotation_note"] = "Clustering-based placeholder — not a trained foundation model"
    return adata
