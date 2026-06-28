"""Active learning hooks (placeholder for future labeling loops)."""

from __future__ import annotations

from typing import Any, Dict, List


def suggest_label_candidates(scores: List[float], top_k: int = 5) -> List[int]:
    """Return indices of uncertain samples (mid-range scores)."""
    if not scores:
        return []
    paired = sorted(enumerate(scores), key=lambda x: abs(x[1] - 0.5))
    return [i for i, _ in paired[:top_k]]


def record_label(module: str, sample_id: str, label: Any) -> Dict[str, Any]:
    return {"module": module, "sample_id": sample_id, "label": label, "stored": True}
