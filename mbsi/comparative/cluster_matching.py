"""Exploratory cluster correspondence based on shared gene signatures."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .preview import _labels, _expression


def cluster_similarity(left, right, left_label: str, right_label: str,
                       genes: list[str], max_clusters: int = 100) -> pd.DataFrame:
    """Cosine similarity between cluster mean profiles on selected genes.

    This is NOT an automatic validated cell-type correspondence algorithm.
    Returns similarity for ALL cluster pairs, including unmatched clusters.
    """
    if not genes:
        raise ValueError("Select at least one gene")
    if any(g not in left.var_names or g not in right.var_names for g in genes):
        raise ValueError("Selected genes must occur in both tissues")
    names_a = _labels(left, left_label).to_numpy()
    names_b = _labels(right, right_label).to_numpy()
    ua, ub = sorted(set(names_a)), sorted(set(names_b))
    if len(ua) > max_clusters or len(ub) > max_clusters:
        raise ValueError("Too many clusters for comparison preview")
    expression_a = _expression(left, genes)
    expression_b = _expression(right, genes)
    profiles_a = np.vstack([expression_a[names_a == name].mean(axis=0) for name in ua])
    profiles_b = np.vstack([expression_b[names_b == name].mean(axis=0) for name in ub])
    # Center per gene across clusters to emphasize signatures rather than depth.
    all_profiles = np.vstack([profiles_a, profiles_b])
    scale = all_profiles.std(axis=0)
    keep = scale > 1e-12
    if not keep.any():
        raise ValueError("Selected genes have no between-cluster variation")
    center = all_profiles[:, keep].mean(axis=0)
    a = (profiles_a[:, keep] - center) / scale[keep]
    b = (profiles_b[:, keep] - center) / scale[keep]
    na = np.linalg.norm(a, axis=1)
    nb = np.linalg.norm(b, axis=1)
    similarity = np.divide(a @ b.T, na[:, None] * nb[None, :],
                           out=np.zeros((len(ua), len(ub))),
                           where=(na[:, None] * nb[None, :]) > 0)
    return pd.DataFrame(similarity, index=ua, columns=ub)
