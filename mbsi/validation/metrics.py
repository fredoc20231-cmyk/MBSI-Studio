"""Extended validation suite."""

from typing import Any, Dict, Optional

import anndata as ad

from mbsi.benchmarks.metrics import compute_all_metrics
from mbsi.boundaries.leakage import compute_boundary_leakage


def run_validation_suite(
    true_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData,
    pseudo_spot_adata: Optional[ad.AnnData] = None,
) -> Dict[str, Any]:
    """Run full validation including leakage benchmark."""
    metrics = compute_all_metrics(true_adata, reconstructed_adata, pseudo_spot_adata)
    metrics["boundary_leakage_recon"] = compute_boundary_leakage(reconstructed_adata)
    return metrics


def run_leakage_benchmark(adata: ad.AnnData) -> float:
    return compute_boundary_leakage(adata)
