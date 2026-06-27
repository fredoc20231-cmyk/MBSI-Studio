#!/usr/bin/env python3
"""
End-to-end smoke test for MBSI Studio platform.

Usage:
    python scripts/smoke_test_platform.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / "data" / "outputs"
OUTPUT.mkdir(parents=True, exist_ok=True)


def main():
    import anndata as ad
    import numpy as np

    from app.components.demo_data import generate_dashboard_demo
    from app.components.cards import export_all

    demo = generate_dashboard_demo(seed=42)
    export_all(demo, OUTPUT)
    print("0. Dashboard demo generated and exported")

    from mbsi.reconstruction.solver import run_mbsi
    from mbsi.segmentation import assign_spots_to_compartments, voronoi_cell_regions
    from mbsi.boundaries import detect_tissue_boundaries, compute_boundary_leakage
    from mbsi.communication import compute_ligand_diffusion_field, build_spatial_signaling_graph
    from mbsi.causal import build_spatial_causal_dag, run_spatial_intervention
    from mbsi.validation import run_validation_suite
    from mbsi.copilot.report_text import generate_results_text

    demo_dir = ROOT / "data" / "demo" / "advanced"
    if (demo_dir / "pseudo_visium_spots.h5ad").exists():
        spot_adata = ad.read_h5ad(demo_dir / "pseudo_visium_spots.h5ad")
        true_adata = ad.read_h5ad(demo_dir / "true_single_cell.h5ad")
    else:
        print("Demo not found; generating minimal synthetic data...")
        n_spots, n_genes = 30, 40
        X = np.random.poisson(3, (n_spots, n_genes)).astype(np.float32)
        spot_adata = ad.AnnData(X=X)
        spot_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
        spot_adata.obs_names = [f"spot_{i}" for i in range(n_spots)]
        spot_adata.obsm["spatial"] = np.random.randn(n_spots, 2) * 50 + 100
        true_adata = None

    print("1. Demo data loaded")
    spot_adata.write_h5ad(OUTPUT / "smoke_spots.h5ad")

    print("2. Running MBSI...")
    reconstructed = run_mbsi(
        spot_adata, n_cells_per_spot=3, max_iter=50, use_anisotropic=False, random_state=42
    )
    reconstructed.write_h5ad(OUTPUT / "smoke_reconstructed.h5ad")

    print("3. Segmentation (Voronoi fallback)...")
    regions = voronoi_cell_regions(spot_adata.obsm["spatial"])
    spot_adata = assign_spots_to_compartments(spot_adata, regions)

    print("4. Boundary detection...")
    boundaries = detect_tissue_boundaries(reconstructed)
    leakage = compute_boundary_leakage(reconstructed, boundaries=boundaries)

    print("5. Communication physics...")
    ligands = [g for g in ["TGFB1", "CXCL12", "gene_0"] if g in reconstructed.var_names][:2]
    if not ligands:
        ligands = [reconstructed.var_names[0]]
    field = compute_ligand_diffusion_field(reconstructed, ligands)
    pairs = [(ligands[0], reconstructed.var_names[min(1, reconstructed.n_vars - 1)])]
    graph = build_spatial_signaling_graph(reconstructed, pairs)

    print("6. Causal model...")
    dag = build_spatial_causal_dag(reconstructed)
    target = list(dag.nodes())[0] if dag.nodes() else "compartment"
    intervention = run_spatial_intervention(dag, target, 0.0)

    print("7. Validation benchmark...")
    if true_adata is not None:
        metrics = run_validation_suite(true_adata, reconstructed, spot_adata)
    else:
        metrics = {"smoke": True, "leakage": leakage, "n_edges": graph.get("n_edges", 0)}
    (OUTPUT / "smoke_metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    print("8. Export report...")
    report_html = (
        "<html><body><h1>MBSI Studio Smoke Report</h1>"
        f"<pre>{generate_results_text(metrics)}</pre></body></html>"
    )
    (OUTPUT / "smoke_report.html").write_text(report_html)

    summary = {
        "n_spots": spot_adata.n_obs,
        "n_cells": reconstructed.n_obs,
        "leakage": leakage,
        "causal_nodes": len(dag.nodes()),
        "intervention_target": target,
    }
    (OUTPUT / "smoke_summary.json").write_text(json.dumps(summary, indent=2))
    print("MBSI Studio smoke test passed.")


if __name__ == "__main__":
    main()
