"""Base adapter interface for benchmark methods."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

import anndata as ad
import numpy as np
from scipy.spatial import KDTree

from mbsi.utils import to_dense_array


@dataclass
class AdapterResult:
    reconstructed_adata: ad.AnnData
    method: str
    method_type: str  # "full" | "proxy" | "unavailable"
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseBenchmarkAdapter(ABC):
    """Consistent interface: ground truth + pseudo-visium → reconstruction."""

    name: str = "base"
    method_type: str = "proxy"

    @abstractmethod
    def run(
        self,
        ground_truth_adata: ad.AnnData,
        pseudo_visium_adata: ad.AnnData,
    ) -> AdapterResult:
        """Run reconstruction and return AdapterResult."""

    def _proxy_knn_from_spots(
        self,
        ground_truth_adata: ad.AnnData,
        pseudo_visium_adata: ad.AnnData,
        k: int = 3,
        label: str = "baseline_proxy",
    ) -> ad.AnnData:
        """kNN spatial interpolation from spot expression to true cell locations."""
        spot_coords = pseudo_visium_adata.obsm["spatial"]
        cell_coords = ground_truth_adata.obsm["spatial"]
        spot_x = to_dense_array(pseudo_visium_adata.X)

        tree = KDTree(spot_coords)
        k_use = min(k, pseudo_visium_adata.n_obs)
        dists, indices = tree.query(cell_coords, k=k_use)

        n_cells = ground_truth_adata.n_obs
        n_genes = pseudo_visium_adata.n_vars
        cell_x = np.zeros((n_cells, n_genes), dtype=np.float32)
        for i in range(n_cells):
            w = 1.0 / (dists[i] + 1e-6)
            w = w / w.sum()
            for j, spot_idx in enumerate(np.atleast_1d(indices[i])):
                cell_x[i] += w[j] * spot_x[spot_idx]

        out = ad.AnnData(X=cell_x)
        out.var_names = pseudo_visium_adata.var_names.copy()
        out.obs_names = ground_truth_adata.obs_names.copy()
        out.obsm["spatial"] = cell_coords.copy()
        if "cell_type" in ground_truth_adata.obs.columns:
            out.obs["cell_type"] = ground_truth_adata.obs["cell_type"].values
        out.uns["method"] = label
        out.uns["method_type"] = "proxy"
        return out
