"""Report output registry for SaaS workspaces."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

_registry: Dict[str, List[Dict[str, Any]]] = {"figures": [], "tables": []}


def register_figure(module: str, title: str, fig: Any) -> None:
    _registry["figures"].append({
        "module": module,
        "title": title,
        "type": "plotly",
        "ref": str(id(fig)),
    })


def register_table(module: str, title: str, df: pd.DataFrame) -> None:
    _registry["tables"].append({
        "module": module,
        "title": title,
        "rows": len(df),
        "columns": list(df.columns),
    })


def get_registered_outputs() -> Dict[str, List[Dict[str, Any]]]:
    return {"figures": list(_registry["figures"]), "tables": list(_registry["tables"])}


def clear_registry() -> None:
    _registry["figures"].clear()
    _registry["tables"].clear()
