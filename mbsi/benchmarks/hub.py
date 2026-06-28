"""Benchmark Hub orchestrator."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any, Dict, List, Optional

import anndata as ad

from mbsi.benchmarks.adapters import get_adapter, list_adapters
from mbsi.benchmarks.leaderboard import build_leaderboard, leaderboard_summary
from mbsi.benchmarks.metrics import compute_benchmark_metrics
from mbsi.benchmarks.pseudo_visium import generate_pseudo_visium, make_synthetic_ground_truth
from mbsi.benchmarks.real_ground_truth import resolve_ground_truth_adata
from mbsi.benchmarks.datasets import validate_single_cell_spatial_ground_truth

BENCHMARK_GUARDRAIL = (
    "Benchmark outputs are computational estimates for research use only. "
    "Proxy methods are labeled baseline_proxy and are not vendor implementations."
)

VC_BANNER = "Every reconstruction claim is benchmarked against single-cell ground truth."


def run_benchmark_hub(
    ground_truth_adata: Optional[ad.AnnData] = None,
    methods: Optional[List[str]] = None,
    platform: str = "xenium",
    seed: int = 42,
    n_spots: int = 80,
    synthetic_cells: int = 200,
    dataset_mode: str = "synthetic",
    uploaded_path: Optional[str] = None,
    session_adata: Optional[ad.AnnData] = None,
) -> Dict[str, Any]:
    """
    Run Benchmark Hub: pseudo-visium → each method → metrics → leaderboard.

    Supports synthetic, upload, or session ground truth modes.
    """
    dataset_meta = {}
    if ground_truth_adata is None:
        ground_truth_adata, dataset_meta = resolve_ground_truth_adata(
            mode=dataset_mode,
            uploaded_path=uploaded_path,
            session_adata=session_adata,
            seed=seed,
            n_cells=synthetic_cells,
        )
    else:
        from mbsi.benchmarks.datasets import prepare_ground_truth_for_benchmark
        ground_truth_adata = prepare_ground_truth_for_benchmark(ground_truth_adata)
        dataset_meta = {
            "mode": "provided",
            "validation": validate_single_cell_spatial_ground_truth(ground_truth_adata),
        }

    readiness = dataset_meta.get("validation", validate_single_cell_spatial_ground_truth(ground_truth_adata))
    pseudo_visium = generate_pseudo_visium(
        ground_truth_adata,
        n_spots=min(n_spots, max(20, ground_truth_adata.n_obs // 3)),
        platform=platform,
        seed=seed,
    )

    method_names = methods or list_adapters()
    results: List[Dict[str, Any]] = []

    for name in method_names:
        adapter = get_adapter(name)
        tracemalloc.start()
        t0 = time.perf_counter()
        try:
            adapter_result = adapter.run(ground_truth_adata, pseudo_visium)
            recon = adapter_result.reconstructed_adata
            status = "ok"
            error = ""
        except Exception as exc:
            recon = None
            status = "error"
            error = str(exc)
            adapter_result = None
        runtime_sec = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_memory_mb = peak / (1024 * 1024)

        if recon is not None:
            metrics = compute_benchmark_metrics(
                ground_truth_adata,
                recon,
                pseudo_spot_adata=pseudo_visium,
                runtime_sec=runtime_sec,
                peak_memory_mb=peak_memory_mb,
            )
            row = {
                "method": adapter_result.method,
                "method_type": adapter_result.method_type,
                "status": status,
                "notes": adapter_result.notes,
                **metrics,
            }
        else:
            row = {
                "method": name,
                "method_type": getattr(adapter, "method_type", "unavailable"),
                "status": status,
                "error": error,
                "runtime_sec": runtime_sec,
                "peak_memory_mb": peak_memory_mb,
            }
        results.append(row)

    leaderboard = build_leaderboard([r for r in results if r.get("status") == "ok"])

    return {
        "ground_truth": ground_truth_adata,
        "pseudo_visium": pseudo_visium,
        "results": results,
        "leaderboard": leaderboard,
        "platform": platform,
        "seed": seed,
        "dataset_mode": dataset_meta.get("mode", dataset_mode),
        "readiness_score": readiness.get("readiness_score", 0),
        "readiness": readiness,
        "dataset_meta": dataset_meta,
        "summary_text": leaderboard_summary(leaderboard),
        "guardrail": BENCHMARK_GUARDRAIL,
        "vc_banner": VC_BANNER,
    }
