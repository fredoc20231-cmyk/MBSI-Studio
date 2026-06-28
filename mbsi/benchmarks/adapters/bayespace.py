"""BayesSpace adapter — baseline proxy."""

from __future__ import annotations

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter


class BayesSpaceAdapter(BaseBenchmarkAdapter):
    name = "bayespace"
    method_type = "proxy"

    def run(self, ground_truth_adata, pseudo_visium_adata) -> AdapterResult:
        recon = self._proxy_knn_from_spots(
            ground_truth_adata,
            pseudo_visium_adata,
            k=6,
            label="bayespace_baseline_proxy",
        )
        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type="proxy",
            notes="BayesSpace (R) unavailable in Python hub; grid kNN baseline_proxy.",
        )
