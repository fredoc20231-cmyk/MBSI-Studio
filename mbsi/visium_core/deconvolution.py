"""Phase 3 — spot deconvolution against a single-cell reference (Tangram / cell2location)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np

from .provenance import BlockedAnalysis, require


def deconvolve(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    ref_path = params.get("reference_h5ad")
    label_key = params.get("reference_label_key", "cell_type")
    if not ref_path or not Path(ref_path).exists():
        raise BlockedAnalysis("No single-cell RNA-seq reference provided.", "Pass params.reference_h5ad pointing to a labelled scRNA-seq .h5ad on the service.")
    ad = require("anndata", "Install anndata.")
    ref = ad.read_h5ad(ref_path)
    if label_key not in ref.obs:
        raise BlockedAnalysis(f"Reference lacks label column '{label_key}'.", "Provide a labelled reference.")
    method = params.get("method", "tangram")
    if method == "tangram":
        tg = require("tangram", "Install tangram-sc.")
        sc = require("scanpy", "Install scanpy.")
        sc.tl.rank_genes_groups(ref, groupby=label_key, use_raw=False)
        markers = np.unique(np.array(ref.uns["rank_genes_groups"]["names"].tolist())[:100].ravel()).tolist()
        tg.pp_adatas(ref, adata, genes=markers)
        amap = tg.map_cells_to_space(ref, adata, mode="clusters", cluster_label=label_key, num_epochs=int(params.get("epochs", 500)), device="cpu")
        tg.project_cell_annotations(amap, adata, annotation=label_key)
        comp = adata.obsm["tangram_ct_pred"]
    elif method == "cell2location":
        raise BlockedAnalysis("cell2location requires a GPU training job; not enabled on this service yet.", "Provision GPU workers and install cell2location.")
    else:
        raise BlockedAnalysis(f"Unknown deconvolution method '{method}'.", "Use tangram or cell2location.")
    comp = comp.div(comp.sum(axis=1), axis=0)
    return {
        "method": method,
        "cell_types": comp.columns.tolist(),
        "mean_composition": comp.mean().round(4).to_dict(),
        "per_spot_composition": comp.head(2000).round(4).to_dict(orient="index"),
        "robustness_note": "Re-run with an independent reference to check concordance before interpreting.",
    }
