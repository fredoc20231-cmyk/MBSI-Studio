#!/usr/bin/env python
"""Run spatially variable gene (SVG) detection on a Visium sample.

Example
-------
    python scripts/run_svg_detection.py \
        --input data/GSM6433585_092A \
        --out results/svg_092A.csv \
        --n-perms 200 --k 6 --n-top 2000

The input directory must follow the Space Ranger ``outs`` layout expected by
``mbsi.io.visium.load_space_ranger`` (a ``filtered_feature_bc_matrix.h5`` plus a
``spatial/`` folder). Outputs a ranked SVG table with Moran's I, Geary's C,
permutation and analytic p-values, and BH-FDR ``is_svg`` calls.
"""

from __future__ import annotations

import argparse

import numpy as np

from mbsi.io.visium import load_space_ranger
from mbsi.analysis import qc, preprocessing as pp
from mbsi.analysis.svg import detect_svgs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Space Ranger sample directory")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--method", default="moran", choices=["moran", "geary"])
    ap.add_argument("--k", type=int, default=6, help="kNN spatial neighbours")
    ap.add_argument("--n-perms", type=int, default=200, help="permutations (0=analytic only)")
    ap.add_argument("--n-top", type=int, default=2000, help="max HVGs to test")
    ap.add_argument("--fdr-alpha", type=float, default=0.05)
    ap.add_argument("--min-spots", type=int, default=3, help="drop genes below this many spots")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    adata, meta = load_space_ranger(args.input)
    print(f"Loaded {adata.shape[0]} spots x {adata.shape[1]} genes "
          f"(platform={meta.get('platform')}, readiness={meta.get('readiness_score')})")

    adata = qc.filter_in_tissue(adata)
    adata = qc.compute_qc_metrics(adata)
    counts = np.asarray((adata.X > 0).sum(axis=0)).ravel()
    adata = adata[:, counts >= args.min_spots].copy()
    adata = pp.normalize_log_transform(adata)
    adata = pp.select_hvgs(adata, n_top_genes=args.n_top)

    res = detect_svgs(
        adata, layer="logcounts", k=args.k, method=args.method,
        n_perms=args.n_perms, fdr_alpha=args.fdr_alpha,
        n_top=args.n_top, random_state=args.seed,
    )
    res.to_csv(args.out, index=False)
    n_sig = int(res["is_svg"].sum())
    print(f"Detected {n_sig}/{len(res)} SVGs at FDR<{args.fdr_alpha}. "
          f"Wrote {args.out}")
    print("Top 10:", ", ".join(res["gene"].head(10)))


if __name__ == "__main__":
    main()
