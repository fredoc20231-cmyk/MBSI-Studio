"""Progress tracking helpers for download jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


ProgressCallback = Callable[[int, int, str], None]


@dataclass
class ProgressTracker:
    """Track byte-level progress for a single file or job aggregate."""

    total_bytes: int = 0
    downloaded_bytes: int = 0
    current_file: str = ""
    n_files: int = 0
    n_complete: int = 0
    events: list[Dict[str, Any]] = field(default_factory=list)

    def start_file(self, filename: str, total: int = 0) -> None:
        self.current_file = filename
        if total > 0:
            self.total_bytes = max(self.total_bytes, total)

    def update(self, chunk_bytes: int, file_total: int = 0, filename: str = "") -> None:
        self.downloaded_bytes += chunk_bytes
        if file_total > 0:
            self.total_bytes = max(self.total_bytes, file_total)
        if filename:
            self.current_file = filename

    def complete_file(self, filename: str) -> None:
        self.n_complete += 1
        self.events.append({"type": "file_complete", "filename": filename})

    def fraction(self) -> float:
        if self.total_bytes <= 0:
            if self.n_files <= 0:
                return 0.0
            return self.n_complete / self.n_files
        return min(1.0, self.downloaded_bytes / self.total_bytes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
            "current_file": self.current_file,
            "n_files": self.n_files,
            "n_complete": self.n_complete,
            "fraction": self.fraction(),
        }


def make_progress_callback(
    tracker: Optional[ProgressTracker] = None,
    on_update: Optional[ProgressCallback] = None,
) -> ProgressCallback:
    """Build a callback invoked as (bytes_downloaded, bytes_total, filename)."""

    def _cb(downloaded: int, total: int, filename: str) -> None:
        if tracker is not None:
            tracker.update(downloaded, total, filename)
        if on_update is not None:
            on_update(downloaded, total, filename)

    return _cb
