"""Report output registry and Results Notebook entries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

_registry: Dict[str, List[Dict[str, Any]]] = {"figures": [], "tables": [], "findings": []}
_notebook_entries: List[Dict[str, Any]] = []
_seq = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id() -> int:
    global _seq
    _seq += 1
    return _seq


def _append_notebook(entry: Dict[str, Any]) -> None:
    entry = dict(entry)
    entry.setdefault("timestamp", _utc_now())
    entry.setdefault("id", _next_id())
    _notebook_entries.append(entry)


def register_figure(module: str, title: str, fig: Any, section: str = "figures") -> None:
    entry = {
        "type": "figure",
        "module": module,
        "section": section,
        "title": title,
        "plotly_type": "plotly",
        "ref": str(id(fig)),
        "timestamp": _utc_now(),
        "id": _next_id(),
    }
    _registry["figures"].append(entry)
    _append_notebook(entry)


def register_table(module: str, title: str, df: pd.DataFrame, section: str = "tables") -> None:
    entry = {
        "type": "table",
        "module": module,
        "section": section,
        "title": title,
        "rows": len(df),
        "columns": list(df.columns),
        "timestamp": _utc_now(),
        "id": _next_id(),
    }
    _registry["tables"].append(entry)
    _append_notebook(entry)


def register_finding(text: str, section: str, module: str, title: str = "") -> None:
    entry = {
        "type": "finding",
        "module": module,
        "section": section,
        "title": title or section,
        "text": text,
        "timestamp": _utc_now(),
        "id": _next_id(),
    }
    _registry["findings"].append(entry)
    _append_notebook(entry)


def get_registered_outputs() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "figures": list(_registry["figures"]),
        "tables": list(_registry["tables"]),
        "findings": list(_registry["findings"]),
    }


def get_notebook_entries() -> List[Dict[str, Any]]:
    return sorted(_notebook_entries, key=lambda e: (e.get("timestamp", ""), e.get("id", 0)))


def clear_registry() -> None:
    _registry["figures"].clear()
    _registry["tables"].clear()
    _registry["findings"].clear()
    _notebook_entries.clear()
