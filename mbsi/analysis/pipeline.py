"""End-to-end standard spatial analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad

from mbsi.analysis.qc import compute_qc_metrics, filter_in_tissue, qc_summary_table, flag_low_quality_spots
from mbsi.analysis.preprocessing import normalize_log_transform, select_hvgs, scale_for_pca
from mbsi.analysis.clustering import run_pca, run_neighbors, run_leiden_clustering, run_umap
from mbsi.analysis.markers import rank_cluster_markers
from mbsi.analysis.spatial_stats import spatial_autocorrelation_table

ANALYSIS_GUARDRAIL = (
    "Analytical outputs are computational results for research use only. "
    "Biological and clinical conclusions require independent validation."
)


def run_standard_spatial_analysis(
    adata: ad.AnnData,
    filter_tissue: bool = True,
    min_counts: float = 500,
    min_genes: float = 200,
    max_mito: float = 25.0,
    n_top_genes: int = 2000,
    n_comps: int = 30,
    n_neighbors: int = 80,
    n_pcs: int = 15,
    resolution: float = 1.0,
    spatial_stats_top_n: int = 500,
) -> Dict[str, Any]:
    """Run QC through spatial autocorrelation; return results dict."""
    params = {
        "filter_tissue": filter_tissue,
        "min_counts": min_counts,
        "min_genes": min_genes,
        "max_mito": max_mito,
        "n_top_genes": n_top_genes,
        "n_comps": n_comps,
        "n_neighbors": n_neighbors,
        "n_pcs": n_pcs,
        "resolution": resolution,
        "spatial_stats_top_n": spatial_stats_top_n,
    }

    adata = adata.copy()
    if filter_tissue:
        adata = filter_in_tissue(adata)
    adata = compute_qc_metrics(adata)
    adata = flag_low_quality_spots(adata, min_counts=min_counts, min_genes=min_genes, max_mito=max_mito)
    adata = adata[adata.obs["qc_pass"]].copy()

    qc_summary = qc_summary_table(adata)
    adata = normalize_log_transform(adata)
    adata = select_hvgs(adata, n_top_genes=n_top_genes)
    adata = scale_for_pca(adata)
    adata = run_pca(adata, n_comps=n_comps)
    adata = run_neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)
    adata = run_leiden_clustering(adata, resolution=resolution)
    adata = run_umap(adata)

    markers = rank_cluster_markers(adata)
    spatial_stats = spatial_autocorrelation_table(adata, n_top=spatial_stats_top_n)

    return {
        "adata": adata,
        "qc_summary": qc_summary,
        "markers": markers,
        "spatial_stats": spatial_stats,
        "parameters": params,
        "figures_ready": True,
        "guardrail": ANALYSIS_GUARDRAIL,
    }


def export_analysis_results(
    results: Dict[str, Any],
    out_dir: Path = Path("data/outputs"),
) -> Path:
    """Export analysis tables and processed AnnData."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results["qc_summary"].to_csv(out_dir / "qc_summary.csv", index=False)
    results["markers"].to_csv(out_dir / "cluster_markers.csv", index=False)
    results["spatial_stats"].to_csv(out_dir / "spatial_autocorrelation.csv", index=False)
    results["adata"].write_h5ad(out_dir / "processed_adata.h5ad")
    (out_dir / "analysis_parameters.json").write_text(
        json.dumps(results.get("parameters", {}), indent=2)
    )
    return out_dir
