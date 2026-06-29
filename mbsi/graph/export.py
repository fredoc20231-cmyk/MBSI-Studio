"""Export discovery graph as JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union


def export_graph_json(graph: Dict[str, Any], path: Union[str, Path]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, default=str))
    return path
