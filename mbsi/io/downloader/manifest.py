"""Download job manifest schema and persistence."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class UrlEntry:
    url: str
    filename: str
    role: str = "unknown"
    technology_hint: str = "unknown"
    source: str = "generic"
    status: str = "queued"
    bytes_downloaded: int = 0
    bytes_total: int = 0
    local_path: str = ""
    sha256: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UrlEntry":
        return cls(
            url=data.get("url", ""),
            filename=data.get("filename", ""),
            role=data.get("role", data.get("likely_role", "unknown")),
            technology_hint=data.get("technology_hint", "unknown"),
            source=data.get("source", "generic"),
            status=data.get("status", "queued"),
            bytes_downloaded=int(data.get("bytes_downloaded", 0)),
            bytes_total=int(data.get("bytes_total", 0)),
            local_path=data.get("local_path", ""),
            sha256=data.get("sha256", ""),
            error=data.get("error", ""),
        )


@dataclass
class DownloadManifest:
    job_id: str
    project_id: str
    created_at: str
    status: str = "queued"
    urls: List[UrlEntry] = field(default_factory=list)
    output_dir: str = ""
    detected_platform: str = ""
    readiness: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    preview: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "status": self.status,
            "output_dir": self.output_dir,
            "urls": [u.to_dict() for u in self.urls],
            "detected_platform": self.detected_platform,
            "readiness": self.readiness,
            "compatibility": self.compatibility,
            "preview": self.preview,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownloadManifest":
        urls = [UrlEntry.from_dict(u) for u in data.get("urls", [])]
        return cls(
            job_id=data.get("job_id", ""),
            project_id=data.get("project_id", ""),
            created_at=data.get("created_at", _utc_now()),
            status=data.get("status", "queued"),
            urls=urls,
            output_dir=data.get("output_dir", ""),
            detected_platform=data.get("detected_platform", ""),
            readiness=data.get("readiness", {}),
            compatibility=data.get("compatibility", {}),
            preview=data.get("preview", {}),
            warnings=data.get("warnings", []),
        )


def new_job_id() -> str:
    return str(uuid.uuid4())[:12]


def manifest_path(output_dir: Path, job_id: str) -> Path:
    return Path(output_dir) / f"download_manifest_{job_id}.json"


def save_manifest(manifest: DownloadManifest, path: Optional[Path] = None) -> Path:
    out = Path(path) if path else manifest_path(Path(manifest.output_dir), manifest.job_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    return out


def load_manifest(path: Path | str) -> DownloadManifest:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return DownloadManifest.from_dict(data)
