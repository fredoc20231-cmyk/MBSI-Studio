"""GraphST adapter — baseline proxy."""

from __future__ import annotations

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter


class GraphSTAdapter(BaseBenchmarkAdapter):
    name = "graphst"
    method_type = "proxy"

    def run(self, ground_truth_adata, pseudo_visium_adata) -> AdapterResult:
        recon = self._proxy_knn_from_spots(
            ground_truth_adata,
            pseudo_visium_adata,
            k=5,
            label="graphst_baseline_proxy",
        )
        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type="proxy",
            notes="GraphST not installed; graph-style kNN smoothing baseline_proxy.",
        )
