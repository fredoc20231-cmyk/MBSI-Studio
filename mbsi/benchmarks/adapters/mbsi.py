"""MBSI reconstruction adapter (full implementation)."""

from __future__ import annotations

import anndata as ad

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter
from mbsi.reconstruction.solver import run_mbsi


class MBSIAdapter(BaseBenchmarkAdapter):
    name = "mbsi"
    method_type = "full"

    def __init__(self, max_iter: int = 80, n_cells_per_spot: int = 3, random_state: int = 42):
        self.max_iter = max_iter
        self.n_cells_per_spot = n_cells_per_spot
        self.random_state = random_state

    def run(
        self,
        ground_truth_adata: ad.AnnData,
        pseudo_visium_adata: ad.AnnData,
    ) -> AdapterResult:
        cell_coords = ground_truth_adata.obsm["spatial"].copy()
        recon = run_mbsi(
            pseudo_visium_adata,
            cell_coords=cell_coords,
            n_cells_per_spot=self.n_cells_per_spot,
            max_iter=self.max_iter,
            use_anisotropic=False,
            random_state=self.random_state,
        )
        if "cell_type" in ground_truth_adata.obs.columns and "cell_type" not in recon.obs.columns:
            recon.obs["cell_type"] = ground_truth_adata.obs["cell_type"].values[: recon.n_obs]
        recon.uns["method"] = self.name
        recon.uns["method_type"] = self.method_type
        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type=self.method_type,
            notes="MBSI physics-aware reconstruction via optimal transport + sheaf regularization.",
        )
