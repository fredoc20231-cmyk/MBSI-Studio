"""
Metrics for benchmarking reconstruction quality.

Computes various metrics to compare reconstructed expression
against ground truth single-cell data.
"""

from typing import Dict, Any, Optional

import anndata as ad
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neighbors import NearestNeighbors

from mbsi.utils import to_dense_array, to_dense_flat


def align_reconstruction_to_truth(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData,
    genes: list
) -> tuple[np.ndarray, np.ndarray]:
    """
    Aggregate reconstructed cells onto true-cell locations via nearest-neighbor assignment.

    Returns expression matrices with shape (n_true_cells, n_genes) for both datasets.
    """
    true_coords = true_adata.obsm['spatial']
    recon_coords = recon_adata.obsm['spatial']

    true_expr = to_dense_array(true_adata[:, genes].X)
    recon_expr = to_dense_array(recon_adata[:, genes].X)

    if true_adata.n_obs == recon_adata.n_obs:
        return true_expr, recon_expr

    k = min(5, recon_adata.n_obs)
    tree = NearestNeighbors(n_neighbors=k).fit(recon_coords)
    _, indices = tree.kneighbors(true_coords)

    aligned_recon = np.zeros((true_adata.n_obs, len(genes)), dtype=np.float64)
    for i in range(true_adata.n_obs):
        aligned_recon[i] = recon_expr[indices[i]].mean(axis=0)

    return true_expr, aligned_recon


def compute_all_metrics(
    true_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData,
    pseudo_spot_adata: Optional[ad.AnnData] = None
) -> Dict[str, Any]:
    """
    Compute all benchmark metrics.
    
    Parameters
    ----------
    true_adata : AnnData
        Ground truth single-cell data
    reconstructed_adata : AnnData
        Reconstructed single-cell data
    pseudo_spot_adata : AnnData, optional
        Pseudo-Visium spot data for additional metrics
        
    Returns
    -------
    metrics : dict
        Dictionary with all computed metrics
    """
    metrics = {}
    
    # Align genes
    common_genes = list(
        set(true_adata.var_names) & set(reconstructed_adata.var_names)
    )
    
    if len(common_genes) == 0:
        return {"error": "No common genes found"}
    
    true_subset = true_adata[:, common_genes].copy()
    recon_subset = reconstructed_adata[:, common_genes].copy()
    
    # Get expression matrices
    X_true = to_dense_array(true_subset.X)
    X_recon = to_dense_array(recon_subset.X)
    
    # Correlation metrics
    metrics['pearson_correlation'] = compute_correlation(X_true, X_recon, method='pearson')
    metrics['spearman_correlation'] = compute_correlation(X_true, X_recon, method='spearman')
    
    # Error metrics
    metrics['rmse'] = compute_rmse(X_true, X_recon)
    metrics['r2_score'] = compute_r2(X_true, X_recon)
    
    # Spatial metrics — align recon cells to true locations when counts differ
    if 'spatial' in true_adata.obsm and 'spatial' in reconstructed_adata.obsm:
        true_spatial, recon_spatial = align_reconstruction_to_truth(
            true_subset, recon_subset, common_genes
        )
        metrics['spatial_correlation'] = compute_spatial_correlation_aligned(
            true_spatial, recon_spatial,
            true_adata.obsm['spatial'],
            common_genes
        )
        metrics['marker_localization'] = compute_marker_localization_aligned(
            true_spatial, recon_spatial
        )
    
    # Boundary leakage
    if 'label' in true_adata.obs and 'label' in reconstructed_adata.obs:
        metrics['boundary_leakage'] = compute_boundary_leakage(
            true_adata, reconstructed_adata
        )
    
    # Moran's I — computed per dataset; preservation compares scalar values
    if 'spatial' in true_adata.obsm and 'spatial' in reconstructed_adata.obsm:
        metrics['morans_i_true'] = compute_morans_i(true_subset)
        _, aligned_expr = align_reconstruction_to_truth(
            true_subset, recon_subset, common_genes
        )
        aligned_for_morans = ad.AnnData(
            X=aligned_expr,
            obsm={'spatial': true_adata.obsm['spatial'].copy()}
        )
        metrics['morans_i_recon'] = compute_morans_i(aligned_for_morans)
        metrics['morans_i_preservation'] = abs(
            metrics['morans_i_true'] - metrics['morans_i_recon']
        )
    else:
        metrics['morans_i_true'] = None
        metrics['morans_i_recon'] = None
        metrics['morans_i_preservation'] = None
    
    # Cell type classification
    if 'cell_type' in true_adata.obs:
        metrics['cell_type_accuracy'] = compute_cell_type_accuracy(
            true_adata, reconstructed_adata
        )
    
    # Spot-level metrics if pseudo-Visium available
    if pseudo_spot_adata is not None:
        from mbsi.benchmarks.pseudo_visium import aggregate_cells_to_spots
        recon_spots = aggregate_cells_to_spots(
            reconstructed_adata,
            pseudo_spot_adata.obsm['spatial']
        )
        
        spot_common_genes = list(
            set(pseudo_spot_adata.var_names) & set(reconstructed_adata.var_names)
        )
        
        if len(spot_common_genes) > 0:
            X_pseudo = pseudo_spot_adata[:, spot_common_genes].X
            gene_idx = [list(reconstructed_adata.var_names).index(g) for g in spot_common_genes]
            X_recon_spots = recon_spots[:, gene_idx]
            
            X_pseudo = to_dense_array(X_pseudo)
            X_recon_spots = to_dense_array(X_recon_spots)
            
            metrics['spot_pearson'] = compute_correlation(X_pseudo, X_recon_spots, 'pearson')
            metrics['spot_rmse'] = compute_rmse(X_pseudo, X_recon_spots)
    
    return metrics


def compute_correlation(
    X_true: np.ndarray,
    X_recon: np.ndarray,
    method: str = 'pearson'
) -> float:
    """
    Compute correlation between true and reconstructed expression.
    
    Parameters
    ----------
    X_true : ndarray
        True expression
    X_recon : ndarray
        Reconstructed expression
    method : str
        'pearson' or 'spearman'
        
    Returns
    -------
    correlation : float
        Mean correlation across genes
    """
    # Handle different sizes by using aggregate statistics
    if X_true.shape[0] != X_recon.shape[0]:
        # Use mean expression per gene for comparison
        true_mean = X_true.mean(axis=0)
        recon_mean = X_recon.mean(axis=0)
        
        if method == 'pearson':
            corr, _ = pearsonr(true_mean, recon_mean)
        else:
            corr, _ = spearmanr(true_mean, recon_mean)
        
        return float(corr) if not np.isnan(corr) else 0.0
    
    # Same size - compute per-gene correlation
    n_genes = X_true.shape[1]
    correlations = []
    
    for g in range(n_genes):
        true_gene = X_true[:, g]
        recon_gene = X_recon[:, g]
        
        # Remove zeros
        mask = (true_gene > 0) | (recon_gene > 0)
        if mask.sum() > 1:
            if method == 'pearson':
                corr, _ = pearsonr(true_gene[mask], recon_gene[mask])
            else:
                corr, _ = spearmanr(true_gene[mask], recon_gene[mask])
            
            if not np.isnan(corr):
                correlations.append(corr)
    
    if len(correlations) > 0:
        return float(np.mean(correlations))
    else:
        return 0.0


def compute_rmse(
    X_true: np.ndarray,
    X_recon: np.ndarray
) -> float:
    """Compute root mean squared error."""
    # Handle different sizes by comparing mean expression
    if X_true.shape != X_recon.shape:
        true_mean = X_true.mean(axis=0)
        recon_mean = X_recon.mean(axis=0)
        return float(np.sqrt(mean_squared_error(true_mean, recon_mean)))
    return float(np.sqrt(mean_squared_error(X_true.flatten(), X_recon.flatten())))


def compute_r2(
    X_true: np.ndarray,
    X_recon: np.ndarray
) -> float:
    """Compute R² score."""
    # Handle different sizes by comparing mean expression
    if X_true.shape != X_recon.shape:
        true_mean = X_true.mean(axis=0)
        recon_mean = X_recon.mean(axis=0)
        return float(r2_score(true_mean, recon_mean))
    return float(r2_score(X_true.flatten(), X_recon.flatten()))


def compute_spatial_correlation(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData,
    genes: list
) -> float:
    """
    Compute spatial correlation of expression patterns.
    
    Parameters
    ----------
    true_adata : AnnData
        True data with spatial coordinates
    recon_adata : AnnData
        Reconstructed data with spatial coordinates
    genes : list
        List of genes to analyze
        
    Returns
    -------
    correlation : float
        Mean spatial correlation
    """
    true_coords = true_adata.obsm['spatial']
    recon_coords = recon_adata.obsm['spatial']
    
    correlations = []
    
    for gene in genes:
        if gene in true_adata.var_names and gene in recon_adata.var_names:
            true_expr = to_dense_flat(true_adata[:, gene].X)
            recon_expr = to_dense_flat(recon_adata[:, gene].X)
            
            # Compute spatial correlation using nearest neighbors
            corr = compute_spatial_autocorr(true_coords, true_expr, recon_coords, recon_expr)
            correlations.append(corr)
    
    return float(np.mean(correlations)) if correlations else 0.0


def compute_spatial_correlation_aligned(
    true_expr: np.ndarray,
    recon_expr: np.ndarray,
    coords: np.ndarray,
    genes: list
) -> float:
    """Spatial correlation on aligned expression matrices sharing coordinates."""
    correlations = []
    for gene_idx in range(min(len(genes), true_expr.shape[1])):
        corr = compute_spatial_autocorr(
            coords, true_expr[:, gene_idx],
            coords, recon_expr[:, gene_idx]
        )
        correlations.append(corr)
    return float(np.mean(correlations)) if correlations else 0.0


def compute_marker_localization_aligned(
    true_expr: np.ndarray,
    recon_expr: np.ndarray,
    top_n: int = 5
) -> float:
    """Marker localization score on aligned expression matrices."""
    gene_vars = np.var(true_expr, axis=0)
    top_indices = np.argsort(gene_vars)[-top_n:][::-1]
    scores = []
    for idx in top_indices:
        corr, _ = pearsonr(true_expr[:, idx], recon_expr[:, idx])
        if not np.isnan(corr):
            scores.append(abs(corr))
    return float(np.mean(scores)) if scores else 0.0


def compute_spatial_autocorr(
    coords1: np.ndarray,
    expr1: np.ndarray,
    coords2: np.ndarray,
    expr2: np.ndarray
) -> float:
    """Compute spatial autocorrelation correlation."""
    # Build KDTree for nearest neighbors
    tree1 = NearestNeighbors(n_neighbors=5).fit(coords1)
    tree2 = NearestNeighbors(n_neighbors=5).fit(coords2)
    
    # Get neighbor similarities
    _, indices1 = tree1.kneighbors(coords1)
    _, indices2 = tree2.kneighbors(coords2)
    
    # Compute mean expression of neighbors
    neighbor_expr1 = np.array([expr1[indices].mean() for indices in indices1])
    neighbor_expr2 = np.array([expr2[indices].mean() for indices in indices2])
    
    # Correlation of neighbor patterns
    corr, _ = pearsonr(neighbor_expr1, neighbor_expr2)
    
    return float(corr) if not np.isnan(corr) else 0.0


def compute_marker_localization(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData,
    genes: list,
    top_n: int = 10
) -> float:
    """
    Compute marker gene localization score.
    
    Measures how well marker genes are localized to correct regions.
    """
    # Identify marker genes using variance-based selection
    X = to_dense_array(true_adata.X)
    gene_vars = np.var(X, axis=0)
    top_gene_indices = np.argsort(gene_vars)[-top_n:][::-1]
    marker_genes = [true_adata.var_names[i] for i in top_gene_indices]
    
    if len(marker_genes) == 0:
        return 0.0
    
    # Compute localization score
    scores = []
    for gene in marker_genes[:5]:
        if gene in recon_adata.var_names:
            true_expr = to_dense_flat(true_adata[:, gene].X)
            recon_expr = to_dense_flat(recon_adata[:, gene].X)
            
            # Correlation as localization score
            corr, _ = pearsonr(true_expr, recon_expr)
            if not np.isnan(corr):
                scores.append(abs(corr))
    
    return float(np.mean(scores)) if scores else 0.0


def compute_boundary_leakage(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData
) -> float:
    """
    Compute boundary leakage score.
    
    Measures expression leakage across compartment boundaries.
    """
    true_labels = true_adata.obs['label'].values
    recon_labels = recon_adata.obs['label'].values
    
    # Simple metric: fraction of cells with mismatched labels
    # (assuming labels should be preserved)
    if len(true_labels) != len(recon_labels):
        return 0.0
    
    mismatch = (true_labels != recon_labels).sum()
    leakage = mismatch / len(true_labels)
    
    return float(leakage)


def compute_morans_i(
    adata: ad.AnnData
) -> float:
    """
    Compute Moran's I spatial autocorrelation.
    
    Simple implementation using nearest neighbors.
    """
    coords = adata.obsm['spatial']
    X = to_dense_array(adata.X)
    
    # Use first gene as example
    expr = X[:, 0]
    
    # Build spatial weights
    tree = NearestNeighbors(n_neighbors=5).fit(coords)
    distances, indices = tree.kneighbors(coords)
    
    # Compute Moran's I
    n = len(expr)
    mean_expr = expr.mean()
    
    numerator = 0.0
    denominator = 0.0
    
    for i in range(n):
        for j_idx, j in enumerate(indices[i]):
            if i != j:
                weight = 1.0 / (distances[i, j_idx] + 1e-10)
                numerator += weight * (expr[i] - mean_expr) * (expr[j] - mean_expr)
        
        denominator += (expr[i] - mean_expr)**2
    
    # Sum of weights
    W = distances.shape[0] * distances.shape[1]
    
    morans_i = (n / W) * (numerator / (denominator + 1e-10))
    
    return float(morans_i)


def compute_cell_type_accuracy(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData
) -> float:
    """
    Compute cell type classification accuracy.
    
    Matches cells by spatial proximity and compares labels.
    """
    if 'cell_type' not in true_adata.obs:
        return 0.0
    
    true_coords = true_adata.obsm['spatial']
    recon_coords = recon_adata.obsm['spatial']
    
    # Find nearest matches
    tree = NearestNeighbors(n_neighbors=1).fit(true_coords)
    _, indices = tree.kneighbors(recon_coords)
    
    # Compare labels
    true_labels = true_adata.obs['cell_type'].values
    recon_labels = recon_adata.obs.get('cell_type', ['unknown'] * len(recon_adata))
    
    correct = 0
    total = len(recon_labels)
    
    for i, true_idx in enumerate(indices.flatten()):
        if recon_labels[i] == true_labels[true_idx]:
            correct += 1
    
    return float(correct / total) if total > 0 else 0.0


def compute_niche_preservation(
    true_adata: ad.AnnData,
    recon_adata: ad.AnnData,
    k: int = 8,
) -> float:
    """Compare local cell-type composition similarity (higher = better)."""
    if "cell_type" not in true_adata.obs.columns:
        return 0.0

    coords = true_adata.obsm["spatial"]
    types = true_adata.obs["cell_type"].astype(str)
    uniq = sorted(types.unique())
    type_to_idx = {t: i for i, t in enumerate(uniq)}
    n = true_adata.n_obs
    true_comp = np.zeros((n, len(uniq)))
    for i, t in enumerate(types):
        true_comp[i, type_to_idx[t]] = 1.0

    tree = NearestNeighbors(n_neighbors=min(k, n)).fit(coords)
    _, idx = tree.kneighbors(coords)
    true_niche = np.array([true_comp[i].mean(axis=0) for i in idx])

    recon_types = recon_adata.obs.get("cell_type", types.iloc[: recon_adata.n_obs])
    if len(recon_types) != n:
        recon_aligned = np.zeros((n, len(uniq)))
        recon_coords = recon_adata.obsm["spatial"]
        rtree = NearestNeighbors(n_neighbors=1).fit(recon_coords)
        _, ridx = rtree.kneighbors(coords)
        for i, j in enumerate(ridx.flatten()):
            rt = str(recon_types.iloc[j]) if hasattr(recon_types, "iloc") else str(recon_types[j])
            if rt in type_to_idx:
                recon_aligned[i, type_to_idx[rt]] = 1.0
    else:
        recon_aligned = np.zeros((n, len(uniq)))
        for i, t in enumerate(recon_types.astype(str)):
            if t in type_to_idx:
                recon_aligned[i, type_to_idx[t]] = 1.0

    recon_niche = np.array([recon_aligned[i].mean(axis=0) for i in idx])
    corrs = []
    for i in range(n):
        a, b = true_niche[i], recon_niche[i]
        if a.std() > 0 and b.std() > 0:
            c, _ = pearsonr(a, b)
            if not np.isnan(c):
                corrs.append(c)
    return float(np.mean(corrs)) if corrs else 0.0


def compute_benchmark_metrics(
    true_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData,
    pseudo_spot_adata: Optional[ad.AnnData] = None,
    runtime_sec: float = 0.0,
    peak_memory_mb: float = 0.0,
) -> Dict[str, Any]:
    """Hub-facing metrics with standardized keys and runtime/memory."""
    base = compute_all_metrics(true_adata, reconstructed_adata, pseudo_spot_adata)
    if "error" in base:
        return {
            "gene_pearson": 0.0,
            "gene_spearman": 0.0,
            "rmse": float("inf"),
            "error": base["error"],
            "runtime_sec": runtime_sec,
            "peak_memory_mb": peak_memory_mb,
        }

    boundary_leak = base.get("boundary_leakage")
    if boundary_leak is None and "cell_type" in true_adata.obs.columns:
        boundary_leak = 1.0 - base.get("cell_type_accuracy", 0.0)

    morans_pres = base.get("morans_i_preservation")
    if morans_pres is not None:
        morans_pres = float(morans_pres)

    return {
        "gene_pearson": float(base.get("pearson_correlation", 0.0)),
        "gene_spearman": float(base.get("spearman_correlation", 0.0)),
        "rmse": float(base.get("rmse", 0.0)),
        "r2_score": float(base.get("r2_score", 0.0)),
        "cell_type_accuracy": float(base.get("cell_type_accuracy", 0.0)),
        "boundary_preservation": float(1.0 - boundary_leak) if boundary_leak is not None else None,
        "niche_preservation": compute_niche_preservation(true_adata, reconstructed_adata),
        "morans_i_preservation": morans_pres,
        "spatial_correlation": base.get("spatial_correlation"),
        "runtime_sec": float(runtime_sec),
        "peak_memory_mb": float(peak_memory_mb),
    }


def benchmark_reconstruction(
    true_adata: ad.AnnData,
    pseudo_spot_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData
) -> Dict[str, Any]:
    """
    Main benchmarking function.
    
    Parameters
    ----------
    true_adata : AnnData
        Ground truth single-cell data
    pseudo_spot_adata : AnnData
        Pseudo-Visium spot data
    reconstructed_adata : AnnData
        Reconstructed single-cell data
        
    Returns
    -------
    metrics : dict
        All benchmark metrics
    """
    return compute_all_metrics(true_adata, reconstructed_adata, pseudo_spot_adata)
