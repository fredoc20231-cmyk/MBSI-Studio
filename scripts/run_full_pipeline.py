"""Run full MBSI Studio pipeline."""

import argparse
import sys
from pathlib import Path

import anndata as ad

sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.pipeline import run_full_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots", default="data/demo/advanced/pseudo_visium_spots.h5ad")
    parser.add_argument("--truth", default="data/demo/advanced/true_single_cell.h5ad")
    parser.add_argument("--output", default="data/outputs/full_pipeline")
    args = parser.parse_args()

    spot_adata = ad.read_h5ad(args.spots)
    true_adata = ad.read_h5ad(args.truth) if Path(args.truth).exists() else None
    state = run_full_pipeline(spot_adata, true_adata=true_adata)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    state["reconstructed"].write_h5ad(out / "reconstructed.h5ad")
    print(f"Pipeline complete. Output: {out}")


if __name__ == "__main__":
    main()
