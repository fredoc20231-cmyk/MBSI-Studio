"""Spatial intervention simulation."""

from typing import Any, Dict

import networkx as nx
import numpy as np


def run_spatial_intervention(
    dag: nx.DiGraph,
    target: str,
    value: float = 0.0,
) -> Dict[str, Any]:
    """
    Clamp target node and propagate effect to descendants (multiplicative decay).
    """
    if target not in dag:
        return {"error": f"Node {target} not in DAG", "effects": {}}

    effects = {target: value}
    for node in nx.descendants(dag, target):
        preds = list(dag.predecessors(node))
        if preds:
            parent_effect = np.mean([effects.get(p, 0) for p in preds if p in effects])
            w = dag.get_edge_data(preds[0], node, {}).get("weight", 0.5)
            effects[node] = float(parent_effect * w * 0.8)
        else:
            effects[node] = 0.0

    return {
        "target": target,
        "intervention_value": value,
        "effects": effects,
        "warning": "Computational hypothesis - Requires experimental validation",
    }
