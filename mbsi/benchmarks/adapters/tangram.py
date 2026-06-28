"""Tangram adapter — baseline proxy when tangram package unavailable."""

from __future__ import annotations

import logging

from mbsi.benchmarks.adapters.base import AdapterResult, BaseBenchmarkAdapter

logger = logging.getLogger(__name__)


class TangramAdapter(BaseBenchmarkAdapter):
    name = "tangram"
    method_type = "proxy"

    def run(self, ground_truth_adata, pseudo_visium_adata) -> AdapterResult:
        try:
            import tangram  # noqa: F401

            self.method_type = "full"
        except ImportError:
            logger.info("tangram package not installed; using proxy adapter")

        recon = self._proxy_knn_from_spots(
            ground_truth_adata,
            pseudo_visium_adata,
            k=3,
            label="tangram_baseline_proxy",
        )
        notes = (
            "tangram package not installed; using kNN spot interpolation baseline_proxy. "
            "Install tangram-sc for full Tangram mapping."
        )
        if self.method_type == "full":
            notes = "Tangram detected but full mapping not wired in hub MVP; using proxy."

        return AdapterResult(
            reconstructed_adata=recon,
            method=self.name,
            method_type="proxy",
            notes=notes,
        )
