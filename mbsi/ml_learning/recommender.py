"""Heuristic next-step recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from mbsi.ml_learning.embeddings import NEXT_MAP
from mbsi.ml_learning.run_store import load_runs

_FEEDBACK = Path(__file__).resolve().parent.parent.parent / "outputs" / "ml_learning_feedback.jsonl"


def recommend_next_analysis(active_module: str) -> List[str]:
    recs = [f"Open **{m}** workspace" for m in NEXT_MAP.get(active_module, ["discovery", "benchmark"])[:3]]
    runs = load_runs(limit=10)
    if not runs:
        recs.append("Run Discovery pipeline for end-to-end outputs")
    return recs


def record_user_feedback(module: str, rating: int) -> None:
    _FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    entry = {"module": module, "rating": int(rating)}
    with _FEEDBACK.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
