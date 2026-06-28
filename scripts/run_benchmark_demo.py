#!/usr/bin/env python3
"""CLI demo for MBSI Benchmark Hub."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT = ROOT / "data" / "outputs"


def main():
    from mbsi.benchmarks.hub import run_benchmark_hub
    from mbsi.benchmarks.export import export_benchmark_hub

    print("MBSI Studio — Benchmark Hub Demo")
    print("=" * 40)

    out = run_benchmark_hub(
        methods=["mbsi", "tangram", "cell2location", "graphst"],
        platform="xenium",
        seed=42,
        n_spots=40,
        synthetic_cells=120,
    )

    export_benchmark_hub(out, out_dir=OUTPUT)
    print(out["summary_text"])
    print(f"\nExports written to {OUTPUT}")


if __name__ == "__main__":
    main()
