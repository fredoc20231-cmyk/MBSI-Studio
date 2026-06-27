"""Run validation suite on demo data."""

import json
import sys
from pathlib import Path

import anndata as ad

sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.validation import run_validation_suite


def main(demo_dir: str = "data/demo/advanced"):
    p = Path(demo_dir)
    true_adata = ad.read_h5ad(p / "true_single_cell.h5ad")
    spot_adata = ad.read_h5ad(p / "pseudo_visium_spots.h5ad")
    recon = ad.read_h5ad(p / "reconstructed.h5ad")
    metrics = run_validation_suite(true_adata, recon, spot_adata)
    out = p / "validation_metrics.json"
    out.write_text(json.dumps(metrics, indent=2, default=str))
    print(f"Validation metrics saved to {out}")
    return metrics


if __name__ == "__main__":
    main()
