"""Synthetic AnnData for TME analysis demos and tests."""

from __future__ import annotations

import anndata as ad
import numpy as np

TME_GENES = [
    "CD8A", "CD3D", "PDCD1", "CD274", "CXCL13", "MS4A1", "BCL6",
    "ACTA2", "FAP", "COL1A1", "VEGFA", "KDR", "PECAM1",
    "HIF1A", "CA9", "SLC2A1", "EPCAM", "KRT8", "MKI67",
]

TME_CELL_TYPES = ["Tumor", "Immune", "CAF", "Endothelial", "Hypoxic_tumor"]


def make_tme_demo_adata(n_spots: int = 100, seed: int = 42) -> ad.AnnData:
    """Synthetic spatial AnnData with TME-relevant genes and cell types."""
    rng = np.random.default_rng(seed)
    side = int(np.ceil(np.sqrt(n_spots)))
    rows, cols = np.divmod(np.arange(n_spots), side)
    coords = np.column_stack([
        cols * 10 + rng.normal(0, 0.5, n_spots),
        rows * 10 + rng.normal(0, 0.5, n_spots),
    ])

    types = rng.choice(TME_CELL_TYPES, size=n_spots, p=[0.35, 0.25, 0.2, 0.1, 0.1])
    n_genes = len(TME_GENES) + 20
    all_genes = TME_GENES + [f"GENE{i}" for i in range(20)]
    X = np.zeros((n_spots, n_genes), dtype=np.float32)

    type_profiles = {
        "Tumor": {"EPCAM": 4, "KRT8": 3, "MKI67": 2},
        "Immune": {"CD8A": 4, "CD3D": 3, "MS4A1": 2, "CXCL13": 2, "BCL6": 1},
        "CAF": {"ACTA2": 4, "FAP": 3, "COL1A1": 3},
        "Endothelial": {"PECAM1": 4, "VEGFA": 2, "KDR": 2},
        "Hypoxic_tumor": {"HIF1A": 4, "CA9": 3, "SLC2A1": 2, "EPCAM": 2},
    }

    for i, ct in enumerate(types):
        base = rng.uniform(0.5, 2.0)
        for j, gene in enumerate(all_genes):
            lam = base
            if gene in type_profiles.get(ct, {}):
                lam = type_profiles[ct][gene] * (1 + 0.3 * np.sin(coords[i, 0] / 15))
            X[i, j] = rng.poisson(max(lam, 0.1))

    adata = ad.AnnData(X=X)
    adata.var_names = all_genes
    adata.obs_names = [f"spot_{i:04d}" for i in range(n_spots)]
    adata.obsm["spatial"] = coords.astype(np.float32)
    adata.obs["cell_type"] = types
    adata.obs["in_tissue"] = np.ones(n_spots, dtype=bool)
    totals = X.sum(axis=1, keepdims=True) + 1e-12
    adata.layers["counts"] = X.copy()
    adata.layers["logcounts"] = np.log1p(X / totals * 1e4)
    adata.uns["platform"] = "synthetic_tme"
    return adata
