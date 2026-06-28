"""SpaHDmap adapter — baseline proxy."""

from __future__ import annotations

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter


class SpaHDmapAdapter(BaseBenchmarkAdapter):
    name = "spahdmap"
    method_type = "proxy"

    def run(self, ground_truth_adata, pseudo_visium_adata) -> AdapterResult:
        recon = self._proxy_knn_from_spots(
            ground_truth_adata,
            pseudo_visium_adata,
            k=4,
            label="spahdmap_baseline_proxy",
        )
        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type="proxy",
            notes="SpaHDmap not installed; HD-map interpolation baseline_proxy.",
        )
