#!/usr/bin/env python3
"""Smoke test for Biopharma Discovery Engine v1."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / "data" / "outputs"
OUTPUT.mkdir(parents=True, exist_ok=True)


def main():
    from mbsi.benchmarks.datasets import validate_single_cell_spatial_ground_truth
    from mbsi.benchmarks.hub import run_benchmark_hub
    from mbsi.communication import run_communication_analysis, make_communication_demo_adata
    from mbsi.tme import run_tme_analysis, make_tme_demo_adata
    from mbsi.discovery import run_discovery_engine, export_discovery_engine
    from mbsi.reports import generate_spatial_biomarker_report, BIOMARKER_DISCLAIMER

    print("1. Benchmark Hub (synthetic)...")
    bench = run_benchmark_hub(methods=["mbsi", "tangram"], seed=42, n_spots=40, synthetic_cells=120)
    assert bench["readiness_score"] >= 60
    print(f"   readiness={bench['readiness_score']}")

    print("2. Communication Intelligence...")
    comm_adata = make_communication_demo_adata(n_spots=60, seed=42)
    comm = run_communication_analysis(comm_adata)
    assert comm["top_pathway"] is not None
    print(f"   top_pathway={comm['top_pathway']}")

    print("3. TME Intelligence...")
    tme_adata = make_tme_demo_adata(n_spots=80, seed=42)
    validation = validate_single_cell_spatial_ground_truth(tme_adata)
    assert validation["readiness_score"] >= 60
    tme = run_tme_analysis(tme_adata)
    assert "program_scores" in tme
    print(f"   niches={len(tme['niches'])}")

    print("4. Discovery Engine orchestrator...")
    discovery = run_discovery_engine(adata=tme_adata, seed=42, benchmark_methods=["mbsi"])
    assert discovery["disclaimer"] == BIOMARKER_DISCLAIMER
    export_discovery_engine(discovery, OUTPUT)
    print(f"   findings={len(discovery['findings'])}")
    assert len(discovery.get("findings", [])) >= 1
    assert "discovery_graph" in discovery

    print("5. Unified biomarker report...")
    report_path = generate_spatial_biomarker_report(
        discovery["benchmark_results"],
        discovery["communication_results"],
        discovery["tme_results"],
        OUTPUT,
    )
    assert report_path.exists()
    assert BIOMARKER_DISCLAIMER in report_path.read_text()
    print(f"   report={report_path}")

    print("\nDiscovery Engine smoke test PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
