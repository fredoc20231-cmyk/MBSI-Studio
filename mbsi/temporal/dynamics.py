"""Estimate spatial dynamics across timepoints."""

from typing import Dict, List

import anndata as ad
import numpy as np

from mbsi.utils import to_dense_array


def estimate_spatial_dynamics(timepoint_adatas: List[ad.AnnData]) -> Dict:
    """
    Estimate compartment expansion, marker change, immune infiltration trends.
    """
    if len(timepoint_adatas) < 2:
        return {"transitions": [], "note": "Need >= 2 timepoints"}

    transitions = []
    for t in range(len(timepoint_adatas) - 1):
        a0, a1 = timepoint_adatas[t], timepoint_adatas[t + 1]
        X0 = to_dense_array(a0.X)
        X1 = to_dense_array(a1.X)
        mean_change = float(np.mean(X1.mean(axis=0) - X0.mean(axis=0)))
        immune_score = 0.0
        if "compartment" in a1.obs:
            immune_score = float((a1.obs["compartment"] == "immune").mean())
        transitions.append({
            "from": t,
            "to": t + 1,
            "mean_expression_change": mean_change,
            "immune_fraction": immune_score,
        })

    return {"transitions": transitions, "note": "Computational hypothesis"}
