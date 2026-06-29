"""Project registry — dataset/run/finding tracking."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ProjectRegistry:
    """Track dataset_id, run_id, finding_ids in JSONL under data/registry/."""

    def __init__(self, registry_dir: Path = Path("data/registry")) -> None:
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.registry_dir / "projects.jsonl"

    def register_run(
        self,
        dataset_id: str,
        finding_ids: List[str],
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        run_id = run_id or str(uuid4())
        record = {
            "dataset_id": dataset_id,
            "run_id": run_id,
            "finding_ids": finding_ids,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        with self._path.open("a") as f:
            f.write(json.dumps(record) + "\n")
        return record

    def list_runs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self._path.exists():
            return []
        runs = []
        for line in self._path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if dataset_id is None or rec.get("dataset_id") == dataset_id:
                runs.append(rec)
        return runs

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        for rec in self.list_runs():
            if rec.get("run_id") == run_id:
                return rec
        return None
