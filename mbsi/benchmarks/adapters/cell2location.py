"""cell2location adapter — baseline proxy."""

from __future__ import annotations

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter


class Cell2locationAdapter(BaseBenchmarkAdapter):
    name = "cell2location"
    method_type = "proxy"

    def run(self, ground_truth_adata, pseudo_visium_adata) -> AdapterResult:
        recon = self._proxy_knn_from_spots(
            ground_truth_adata,
            pseudo_visium_adata,
            k=4,
            label="cell2location_baseline_proxy",
        )
        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type="proxy",
            notes="cell2location not installed; spatial kNN deconvolution baseline_proxy.",
        )
