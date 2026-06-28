"""Local run history store for ML learning layer."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_STORE = Path(__file__).resolve().parent.parent.parent / "outputs" / "ml_learning_runs.jsonl"


def log_analysis_run(module: str, run_name: str, metadata: Dict[str, Any] | None = None) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "module": module,
        "run_name": run_name,
        "metadata": metadata or {},
    }
    with _STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load_runs(limit: int = 50) -> List[Dict[str, Any]]:
    if not _STORE.exists():
        return []
    lines = _STORE.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
