"""Seurat-like analysis layer — delegates to mbsi.analysis where possible."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad

from mbsi.analysis.seurat_like.qc import filter_cells_or_spots, run_qc
from mbsi.analysis.seurat_like.normalization import normalize_log1p, run_sctransform_like
from mbsi.analysis.seurat_like.variable_features import find_variable_features
from mbsi.analysis.seurat_like.reduction import run_neighbors, run_pca, run_tsne, run_umap, scale_data
from mbsi.analysis.seurat_like.clustering import run_leiden, run_louvain
from mbsi.analysis.seurat_like.markers import find_cluster_markers
from mbsi.analysis.seurat_like.differential_expression import run_differential_expression
from mbsi.profiles.scalability import scalability_mode
from mbsi.profiles.seurat_like import get_workflow_preset
from mbsi.scalability.memory import estimate_memory


def run_seurat_like_pipeline(
    adata: ad.AnnData,
    preset: str = "basic_unsupervised",
    min_counts: float = 500,
    min_genes: float = 200,
    max_mito: float = 25.0,
    n_top_genes: Optional[int] = None,
    n_comps: Optional[int] = None,
    n_neighbors: Optional[int] = None,
    n_pcs: Optional[int] = None,
    resolution: Optional[float] = None,
    clustering_method: str = "Leiden",
    normalization: Optional[str] = None,
    filter_tissue: bool = True,
) -> Dict[str, Any]:
    """Run full Seurat-like pipeline; return results dict with warnings."""
    cfg = get_workflow_preset(preset)
    n_top_genes = n_top_genes or cfg.get("n_top_genes", 2000)
    n_comps = n_comps or cfg.get("n_comps", 30)
    n_neighbors = n_neighbors or cfg.get("n_neighbors", 30)
    n_pcs = n_pcs or cfg.get("n_pcs", 15)
    resolution = resolution if resolution is not None else cfg.get("resolution", 1.0)
    norm_method = normalization or cfg.get("normalization", "log1p")

    warnings: List[str] = []
    mode = scalability_mode(adata.n_obs)
    mem = estimate_memory(adata)
    if mode != "in_memory":
        warnings.append(f"Large dataset detected — using {mode} mode (est. {mem['total_gb']:.1f} GB).")

    adata, qc_summary, qc_warnings = run_qc(
        adata,
        min_counts=min_counts,
        min_genes=min_genes,
        max_mito=max_mito,
        filter_tissue=filter_tissue,
    )
    warnings.extend(qc_warnings)

    if norm_method == "sctransform_like":
        adata, norm_note = run_sctransform_like(adata)
        warnings.append(norm_note)
    else:
        adata = normalize_log1p(adata)

    adata = find_variable_features(adata, n_top_genes=n_top_genes)
    adata = scale_data(adata)
    adata = run_pca(adata, n_comps=n_comps)
    adata = run_neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)

    method_key = clustering_method.lower()
    if "louvain" in method_key:
        adata, cluster_note = run_louvain(adata, resolution=resolution)
    else:
        adata, cluster_note = run_leiden(adata, resolution=resolution)
    if cluster_note:
        warnings.append(cluster_note)

    adata = run_umap(adata, n_pcs=n_pcs)
    markers = find_cluster_markers(adata)
    de_results = run_differential_expression(adata)

    return {
        "adata": adata,
        "qc_summary": qc_summary,
        "markers": markers,
        "de_results": de_results,
        "warnings": warnings,
        "scalability_mode": mode,
        "memory_estimate": mem,
        "parameters": {
            "preset": preset,
            "min_counts": min_counts,
            "min_genes": min_genes,
            "max_mito": max_mito,
            "n_top_genes": n_top_genes,
            "n_comps": n_comps,
            "n_neighbors": n_neighbors,
            "n_pcs": n_pcs,
            "resolution": resolution,
            "clustering_method": clustering_method,
            "normalization": norm_method,
        },
    }


__all__ = [
    "run_seurat_like_pipeline",
    "run_qc",
    "filter_cells_or_spots",
    "normalize_log1p",
    "run_sctransform_like",
    "find_variable_features",
    "scale_data",
    "run_pca",
    "run_neighbors",
    "run_umap",
    "run_tsne",
    "run_leiden",
    "run_louvain",
    "find_cluster_markers",
    "run_differential_expression",
]
