"""Cell phenotyping — marker panels, atlas mapping, TME scores."""

from __future__ import annotations

from typing import Tuple

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.references.marker_panels import get_panel, list_panels
from mbsi.references.atlas_registry import get_atlas_metadata, list_atlases


def score_marker_panel(adata: ad.AnnData, panel_name: str) -> Tuple[ad.AnnData, pd.DataFrame]:
    """Score cells/spots using reference marker panel."""
    adata = adata.copy()
    markers = get_panel(panel_name) if panel_name.lower() in [p.lower() for p in list_panels()] else []
    if not markers:
        markers = [g for g in adata.var_names[:5]]
    present = [g for g in markers if g in adata.var_names]
    if not present:
        return adata, pd.DataFrame()

    X = adata[:, present].X
    if hasattr(X, "toarray"):
        X = X.toarray()
    score = np.asarray(X, dtype=float).mean(axis=1)
    col = f"panel_{panel_name.replace(' ', '_')[:30]}"
    adata.obs[col] = score
    summary = pd.DataFrame({"panel": [panel_name], "n_markers": [len(present)], "mean_score": [float(score.mean())]})
    return adata, summary


def map_atlas(adata: ad.AnnData, atlas_name: str) -> Tuple[ad.AnnData, pd.DataFrame]:
    """Atlas mapping stub — assigns labels from atlas registry metadata."""
    adata = adata.copy()
    meta = get_atlas_metadata(atlas_name) if atlas_name in list_atlases() else {}
    label = meta.get("label_key", "unassigned") if meta else "unassigned"
    adata.obs["atlas_label"] = label
    summary = pd.DataFrame({"atlas": [atlas_name], "label": [label], "n_spots": [adata.n_obs]})
    return adata, summary


def score_tme(adata: ad.AnnData) -> Tuple[ad.AnnData, pd.DataFrame]:
    """TME compartment scores using immune/stromal/epithelial panels."""
    rows = []
    for panel in ("immune", "stromal", "epithelial"):
        adata, summ = score_marker_panel(adata, panel)
        if not summ.empty:
            rows.append({"compartment": panel, **summ.iloc[0].to_dict()})
    return adata, pd.DataFrame(rows)
