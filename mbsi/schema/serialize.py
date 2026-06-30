"""JSON serialization helpers for MBSI schema entities."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union


def _default_encoder(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def to_json_serializable(obj: Any) -> Any:
    """Recursively convert schema objects to JSON-safe structures."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return to_json_serializable(obj.to_dict())
    if is_dataclass(obj) and not isinstance(obj, type):
        return to_json_serializable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [to_json_serializable(v) for v in obj]
    return str(obj)


def dumps(obj: Any, *, indent: int = 2) -> str:
    return json.dumps(to_json_serializable(obj), indent=indent, default=_default_encoder)


def dump(obj: Any, path: Union[str, Path]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps(obj))
    return out


def loads(text: str) -> Any:
    return json.loads(text)


def entity_list_to_dicts(items: Iterable[Any]) -> List[Dict[str, Any]]:
    return [to_json_serializable(item) for item in items]
