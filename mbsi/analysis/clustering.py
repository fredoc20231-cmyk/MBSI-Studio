"""PCA, neighbors, clustering, UMAP."""

from __future__ import annotations

import anndata as ad
import numpy as np
from scipy import sparse
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


def run_neighbors(adata: ad.AnnData, n_neighbors: int = 15, n_pcs: int = 15) -> ad.AnnData:
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
        return adata, "Leiden (igraph on expression connectivities)"

    if "louvain" in method_key:
        raise ValueError("BackendUnavailable: Louvain is not configured; no Leiden substitution is permitted.")

    if "spatial graph" in method_key or "spatial_graph" in method_key:
        from mbsi.visium_core.niches import spatial_niches
        spatial_niches(adata, {"resolution": resolution})
        adata.obs[key_added] = adata.obs["spatial_niche"].copy()
        return adata, "Joint expression + spatial graph Leiden"

    if any(name in method_key for name in ("bayesspace", "graphst", "stagate")):
        raise ValueError(f"BackendUnavailable: {method} is not installed; no algorithm substitution permitted.")

    raise ValueError(f"Unknown clustering method: {method}")
    """Run genuine Leiden on the sparse expression-neighbor graph."""
    import scanpy as sc
    adata = adata.copy()
    if "connectivities" not in adata.obsp:
        if "X_pca" not in adata.obsm:
            raise ValueError("Run PCA and neighbors before Leiden clustering")
        adata = run_neighbors(adata)
    sc.tl.leiden(
        adata, adjacency=adata.obsp["connectivities"], resolution=resolution,
        key_added=key_added, flavor="igraph", n_iterations=2, directed=False,
        random_state=0,
    )
    return adata

