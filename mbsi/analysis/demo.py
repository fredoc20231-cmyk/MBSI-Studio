"""Synthetic Visium-like AnnData for demo and tests."""

from __future__ import annotations

import numpy as np
import anndata as ad
from scipy.sparse import csr_matrix


def make_synthetic_visium_adata(
    n_spots: int = 120,
    n_genes: int = 300,
    seed: int = 42,
) -> ad.AnnData:
    """Create synthetic spatial AnnData mimicking filtered Visium spots."""
    rng = np.random.default_rng(seed)
    n_mito = max(5, n_genes // 20)
    gene_names = [f"MT-gene{i}" for i in range(n_mito)] + [
        f"GENE{i}" for i in range(n_mito, n_genes)
    ]

    lam = rng.uniform(2, 8, (n_spots, n_genes))
    X = csr_matrix(rng.poisson(lam).astype(np.float32))

    side = int(np.ceil(np.sqrt(n_spots)))
    rows, cols = np.divmod(np.arange(n_spots), side)
    coords = np.column_stack([
        cols * 10 + rng.normal(0, 0.5, n_spots),
        rows * 10 + rng.normal(0, 0.5, n_spots),
    ])

    adata = ad.AnnData(X=X)
    adata.var_names = gene_names
    adata.obs_names = [f"AAACCCA-{i:04d}-1" for i in range(n_spots)]
    adata.obsm["spatial"] = coords.astype(np.float32)
    adata.obs["in_tissue"] = np.ones(n_spots, dtype=bool)
    adata.obs["array_row"] = rows.astype(int)
    adata.obs["array_col"] = cols.astype(int)
    adata.uns["spatial"] = {
        "library_id": {
            "images": {},
            "scalefactors": {"tissue_hires_scalef": 1.0, "tissue_lowres_scalef": 0.1},
        }
    }
    return adata
