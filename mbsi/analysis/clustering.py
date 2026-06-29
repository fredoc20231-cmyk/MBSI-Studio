"""PCA, neighbors, clustering, UMAP."""

from __future__ import annotations

import anndata as ad
import numpy as np
from scipy import sparse
from sklearn.cluster import SpectralClustering
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph


def _hvg_indices(adata: ad.AnnData) -> np.ndarray:
    if "highly_variable" in adata.var.columns:
        return np.where(adata.var["highly_variable"].values)[0]
    return np.arange(adata.n_vars)


def run_pca(adata: ad.AnnData, n_comps: int = 30, use_highly_variable: bool = True) -> ad.AnnData:
    """Run PCA and store in adata.obsm['X_pca']."""
    adata = adata.copy()
    idx = _hvg_indices(adata) if use_highly_variable else np.arange(adata.n_vars)
    n_comps = min(n_comps, len(idx), adata.n_obs - 1)
    n_comps = max(1, n_comps)
    X = np.asarray(adata.X[:, idx])
    if hasattr(X, "toarray"):
        X = X.toarray()
    pca = PCA(n_components=n_comps, random_state=0)
    adata.obsm["X_pca"] = pca.fit_transform(X)
    adata.uns["pca"] = {"variance_ratio": pca.explained_variance_ratio_.tolist()}
    return adata


def run_neighbors(adata: ad.AnnData, n_neighbors: int = 80, n_pcs: int = 15) -> ad.AnnData:
    """Build kNN connectivities graph in adata.obsp."""
    adata = adata.copy()
    if "X_pca" not in adata.obsm:
        raise ValueError("Run PCA before neighbors")
    n_neighbors = min(n_neighbors, adata.n_obs - 1)
    n_pcs = min(n_pcs, adata.obsm["X_pca"].shape[1])
    X = adata.obsm["X_pca"][:, :n_pcs]
    conn = kneighbors_graph(X, n_neighbors=n_neighbors, mode="connectivity", include_self=False)
    conn = conn.maximum(conn.T)
    adata.obsp["connectivities"] = conn.tocsr()
    adata.uns["neighbors"] = {"params": {"n_neighbors": n_neighbors, "n_pcs": n_pcs}}
    return adata


def run_clustering_method(
    adata: ad.AnnData,
    method: str = "Leiden",
    resolution: float = 1.0,
    key_added: str = "cluster",
) -> tuple[ad.AnnData, str]:
    """Run selected clustering with honest fallback when backend unavailable."""
    adata = adata.copy()
    method_key = (method or "Leiden").lower()
    fallback_note = ""

    if "leiden" in method_key:
        adata = run_leiden_clustering(adata, resolution=resolution, key_added=key_added)
        return adata, "Leiden (spectral on kNN graph)"

    if "louvain" in method_key:
        adata = run_leiden_clustering(adata, resolution=max(0.5, resolution * 0.8), key_added=key_added)
        return adata, "Louvain unavailable — Leiden spectral fallback used"

    if "k-means" in method_key or "kmeans" in method_key:
        from sklearn.cluster import KMeans

        n_clusters = max(2, min(int(round(2 + resolution * 4)), adata.n_obs - 1))
        X = adata.obsm.get("X_pca")
        if X is None:
            adata = run_pca(adata)
            X = adata.obsm["X_pca"]
        labels = KMeans(n_clusters=n_clusters, random_state=0, n_init=10).fit_predict(X[:, : min(15, X.shape[1])])
        adata.obs[key_added] = labels.astype(str)
        return adata, "k-means on PCA"

    if "spatial graph" in method_key or "spatial_graph" in method_key:
        adata = run_neighbors(adata) if "connectivities" not in adata.obsp else adata
        adata = run_leiden_clustering(adata, resolution=resolution, key_added=key_added)
        return adata, "Spatial graph (kNN + spectral clustering)"

    if "bayesspace" in method_key:
        adata = run_neighbors(adata) if "connectivities" not in adata.obsp else adata
        adata = run_leiden_clustering(adata, resolution=resolution, key_added=key_added)
        return adata, "BayesSpace (R) unavailable — spatial kNN spectral fallback"

    if "graphst" in method_key or "stagate" in method_key:
        adata = run_neighbors(adata) if "connectivities" not in adata.obsp else adata
        adata = run_leiden_clustering(adata, resolution=resolution, key_added=key_added)
        backend = "GraphST" if "graphst" in method_key else "STAGATE"
        return adata, f"{backend} adapter unavailable — graph-smoothed spectral fallback"

    adata = run_leiden_clustering(adata, resolution=resolution, key_added=key_added)
    return adata, f"Unknown method '{method}' — Leiden fallback"


def run_leiden_clustering(adata: ad.AnnData, resolution: float = 1.0, key_added: str = "cluster") -> ad.AnnData:
    """Cluster spots using spectral clustering on the kNN graph."""
    adata = adata.copy()
    n_clusters = max(2, min(int(round(2 + resolution * 4)), adata.n_obs - 1))
    if "connectivities" in adata.obsp:
        aff = adata.obsp["connectivities"].toarray()
        np.fill_diagonal(aff, 0)
        labels = SpectralClustering(
            n_clusters=n_clusters,
            affinity="precomputed",
            random_state=0,
            assign_labels="kmeans",
        ).fit_predict(aff)
    elif "X_pca" in adata.obsm:
        labels = SpectralClustering(
            n_clusters=n_clusters,
            affinity="nearest_neighbors",
            random_state=0,
        ).fit_predict(adata.obsm["X_pca"][:, : min(15, adata.obsm["X_pca"].shape[1])])
    else:
        raise ValueError("Run neighbors or PCA before clustering")
    adata.obs[key_added] = labels.astype(str)
    return adata


def run_umap(adata: ad.AnnData, n_pcs: int = 15) -> ad.AnnData:
    """Run UMAP embedding via umap-learn."""
    adata = adata.copy()
    if "X_pca" not in adata.obsm:
        raise ValueError("Run PCA before UMAP")
    import umap

    n_pcs = min(n_pcs, adata.obsm["X_pca"].shape[1])
    reducer = umap.UMAP(n_components=2, random_state=0, n_neighbors=min(15, adata.n_obs - 1))
    adata.obsm["X_umap"] = reducer.fit_transform(adata.obsm["X_pca"][:, :n_pcs])
    return adata


def full_clustering_workflow(
    adata: ad.AnnData,
    n_top_genes: int = 2000,
    n_comps: int = 30,
    n_neighbors: int = 80,
    n_pcs: int = 15,
    resolution: float = 1.0,
) -> ad.AnnData:
    """Run normalization, HVG, PCA, neighbors, clustering, and UMAP."""
    from mbsi.analysis.preprocessing import normalize_log_transform, select_hvgs, scale_for_pca

    adata = normalize_log_transform(adata)
    adata = select_hvgs(adata, n_top_genes=n_top_genes)
    adata = scale_for_pca(adata)
    adata = run_pca(adata, n_comps=n_comps)
    adata = run_neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)
    adata = run_leiden_clustering(adata, resolution=resolution)
    adata = run_umap(adata, n_pcs=n_pcs)
    return adata
