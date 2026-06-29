"""Download job manager — streaming downloads with resume, retry, and concurrency."""

from __future__ import annotations

import hashlib
import socket
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from mbsi.io.downloader.inspector import inspect_downloaded_files, update_ingestion_readiness
from mbsi.io.downloader.manifest import (
    DownloadManifest,
    UrlEntry,
    load_manifest,
    manifest_path,
    new_job_id,
    save_manifest,
)
from mbsi.io.downloader.parse_commands import classify_download_url, parse_url_entries
from mbsi.io.downloader.patch_analyzer import run_incremental_patch_analysis
from mbsi.io.downloader.progress import ProgressCallback

# Job control registry (thread-safe)
_JOB_LOCK = threading.Lock()
_CANCEL_EVENTS: Dict[str, threading.Event] = {}
_ACTIVE_JOBS: Dict[str, threading.Thread] = {}

DEFAULT_CHUNK_SIZE = 256 * 1024
DEFAULT_TIMEOUT = 120
DEFAULT_RETRIES = 3
MAX_WORKERS = 3
LARGE_FILE_WARNING_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

ALLOWLIST_HINT_HOSTS = (
    "10xgenomics.com",
    "cf.10xgenomics.com",
    "vizgen.com",
    "nanostring.com",
    "stomics.tech",
    "github.com",
    "zenodo.org",
    "figshare.com",
    "cellxgene.cziscience.com",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _check_url_warning(url: str) -> Optional[str]:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return "Invalid URL — no hostname"
    if not any(host == h or host.endswith("." + h) for h in ALLOWLIST_HINT_HOSTS):
        return f"URL host '{host}' is not on the common facility allowlist — verify source before downloading"
    return None


def create_download_job(
    project_id: str,
    urls: List[str] | str,
    output_dir: str | Path,
    *,
    parsed_entries: Optional[List[Dict[str, Any]]] = None,
) -> DownloadManifest:
    """Create a queued download job manifest."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    job_id = new_job_id()

    entries = parsed_entries
    if entries is None:
        if isinstance(urls, str):
            entries = parse_url_entries(urls)
        else:
            entries = [classify_download_url(u) for u in urls]

    url_entries: List[UrlEntry] = []
    warnings: List[str] = []
    for info in entries:
        warn = _check_url_warning(info["url"])
        if warn:
            warnings.append(warn)
        url_entries.append(
            UrlEntry(
                url=info["url"],
                filename=info["filename"],
                role=info.get("likely_role", "unknown"),
                technology_hint=info.get("technology_hint", "unknown"),
                source=info.get("source", "generic"),
                status="queued",
            )
        )

    manifest = DownloadManifest(
        job_id=job_id,
        project_id=project_id,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        status="queued",
        urls=url_entries,
        output_dir=str(out.resolve()),
        warnings=list(dict.fromkeys(warnings)),
    )
    save_manifest(manifest)
    return manifest


def download_file(
    url: str,
    dest_path: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    progress_callback: Optional[ProgressCallback] = None,
    cancel_event: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    """
    Stream-download a URL to dest_path with resume support for partial files.

    Returns dict with status, bytes_downloaded, bytes_total, sha256, error.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    partial = dest_path.with_suffix(dest_path.suffix + ".partial")

    resume_from = partial.stat().st_size if partial.exists() else 0
    bytes_downloaded = resume_from
    bytes_total = 0
    last_error = ""

    for attempt in range(1, retries + 1):
        if cancel_event and cancel_event.is_set():
            return {
                "status": "cancelled",
                "bytes_downloaded": bytes_downloaded,
                "bytes_total": bytes_total,
                "sha256": "",
                "error": "cancelled by user",
            }

        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "MBSI-Studio/1.0")
            if resume_from > 0:
                req.add_header("Range", f"bytes={resume_from}-")

            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_length = resp.headers.get("Content-Length")
                if content_length:
                    cl = int(content_length)
                    bytes_total = resume_from + cl if resp.status == 206 else cl

                if resp.status == 416:
                    if partial.exists() and partial.stat().st_size > 0:
                        partial.rename(dest_path)
                        sha = _sha256_file(dest_path)
                        return {
                            "status": "complete",
                            "bytes_downloaded": partial.stat().st_size,
                            "bytes_total": partial.stat().st_size,
                            "sha256": sha,
                            "error": "",
                        }

                mode = "ab" if resume_from > 0 and resp.status == 206 else "wb"
                if mode == "wb":
                    resume_from = 0
                    bytes_downloaded = 0

                with open(partial, mode) as out:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            return {
                                "status": "cancelled",
                                "bytes_downloaded": bytes_downloaded,
                                "bytes_total": bytes_total,
                                "sha256": "",
                                "error": "cancelled by user",
                            }
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out.write(chunk)
                        bytes_downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(bytes_downloaded, bytes_total, dest_path.name)

            partial.rename(dest_path)
            sha = _sha256_file(dest_path)
            final_size = dest_path.stat().st_size
            return {
                "status": "complete",
                "bytes_downloaded": final_size,
                "bytes_total": final_size if not bytes_total else bytes_total,
                "sha256": sha,
                "error": "",
            }

        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, OSError) as exc:
            last_error = str(exc)
            resume_from = partial.stat().st_size if partial.exists() else 0
            bytes_downloaded = resume_from
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
            continue

    return {
        "status": "failed",
        "bytes_downloaded": bytes_downloaded,
        "bytes_total": bytes_total,
        "sha256": "",
        "error": last_error or "download failed",
    }


def _download_one(
    entry: UrlEntry,
    output_dir: Path,
    cancel_event: threading.Event,
    manifest_path_ref: Path,
    job_id: str,
) -> UrlEntry:
    dest = output_dir / entry.filename
    if dest.exists() and dest.stat().st_size > 0:
        entry.status = "complete"
        entry.local_path = str(dest)
        entry.bytes_downloaded = dest.stat().st_size
        entry.bytes_total = entry.bytes_downloaded
        entry.sha256 = _sha256_file(dest)
        return entry

    entry.status = "running"

    def _progress(downloaded: int, total: int, _name: str) -> None:
        entry.bytes_downloaded = downloaded
        if total > 0:
            entry.bytes_total = total
        try:
            m = load_manifest(manifest_path_ref)
            for u in m.urls:
                if u.url == entry.url:
                    u.bytes_downloaded = downloaded
                    u.bytes_total = total
                    u.status = "running"
            save_manifest(m, manifest_path_ref)
        except Exception:
            pass

    result = download_file(
        entry.url,
        dest,
        progress_callback=_progress,
        cancel_event=cancel_event,
    )
    entry.status = result["status"]
    entry.bytes_downloaded = result["bytes_downloaded"]
    entry.bytes_total = result["bytes_total"] or result["bytes_downloaded"]
    entry.sha256 = result.get("sha256", "")
    entry.error = result.get("error", "")
    if result["status"] == "complete":
        entry.local_path = str(dest)
        if entry.bytes_total >= LARGE_FILE_WARNING_BYTES:
            entry.error = entry.error or f"Large file ({entry.bytes_total / 1e9:.1f} GB) — verify disk space"

    return entry


def run_download_job(
    manifest: DownloadManifest | str | Path,
    *,
    max_workers: int = MAX_WORKERS,
    on_file_complete: Optional[Callable[[UrlEntry], None]] = None,
) -> DownloadManifest:
    """Run concurrent downloads for a job manifest."""
    if isinstance(manifest, (str, Path)):
        manifest = load_manifest(manifest)

    mp = manifest_path(Path(manifest.output_dir), manifest.job_id)
    cancel_event = threading.Event()
    with _JOB_LOCK:
        _CANCEL_EVENTS[manifest.job_id] = cancel_event

    manifest.status = "running"
    save_manifest(manifest, mp)

    output_dir = Path(manifest.output_dir)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_download_one, entry, output_dir, cancel_event, mp, manifest.job_id): entry
            for entry in manifest.urls
            if entry.status in ("queued", "failed", "running")
        }

        for fut in as_completed(futures):
            if cancel_event.is_set():
                break
            try:
                updated = fut.result()
                for i, u in enumerate(manifest.urls):
                    if u.url == updated.url:
                        manifest.urls[i] = updated
                        break
                save_manifest(manifest, mp)
                if on_file_complete:
                    on_file_complete(updated)

                preview = run_incremental_patch_analysis(manifest)
                manifest.preview = preview
                ing = update_ingestion_readiness(output_dir)
                manifest.detected_platform = ing["detection"].get("platform", "")
                manifest.readiness = ing["readiness"]
                manifest.compatibility = ing["compatibility"]
                save_manifest(manifest, mp)
            except Exception as exc:
                entry = futures[fut]
                entry.status = "failed"
                entry.error = str(exc)
                save_manifest(manifest, mp)

    if cancel_event.is_set():
        manifest.status = "cancelled"
        for u in manifest.urls:
            if u.status == "running":
                u.status = "cancelled"
    elif any(u.status == "failed" for u in manifest.urls):
        manifest.status = "failed"
    elif all(u.status == "complete" for u in manifest.urls):
        manifest.status = "complete"
    else:
        manifest.status = "running"

    ing = update_ingestion_readiness(output_dir)
    manifest.detected_platform = ing["detection"].get("platform", "")
    manifest.readiness = ing["readiness"]
    manifest.compatibility = ing["compatibility"]
    manifest.preview = run_incremental_patch_analysis(manifest)
    save_manifest(manifest, mp)

    with _JOB_LOCK:
        _CANCEL_EVENTS.pop(manifest.job_id, None)
        _ACTIVE_JOBS.pop(manifest.job_id, None)

    return manifest


def cancel_download_job(job_id: str) -> bool:
    """Signal cancellation for an active download job."""
    with _JOB_LOCK:
        ev = _CANCEL_EVENTS.get(job_id)
        if ev:
            ev.set()
            return True
    return False


def start_download_job_async(
    manifest: DownloadManifest,
    *,
    max_workers: int = MAX_WORKERS,
) -> threading.Thread:
    """Start run_download_job in a background thread (for Streamlit UI)."""

    def _run() -> None:
        run_download_job(manifest, max_workers=max_workers)

    t = threading.Thread(target=_run, daemon=True, name=f"download-{manifest.job_id}")
    with _JOB_LOCK:
        _ACTIVE_JOBS[manifest.job_id] = t
    t.start()
    return t
