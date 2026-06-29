"""Archive listing and zip-slip-safe extraction."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path
from typing import List, Union

ARCHIVE_SUFFIXES = (".zip", ".tar.gz", ".tgz", ".tar")


def is_archive(path: Union[str, Path]) -> bool:
    p = Path(path)
    name = p.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        return True
    return p.suffix.lower() in (".zip", ".tar")


def _safe_member_name(name: str) -> bool:
    normalized = Path(name.replace("\\", "/"))
    return ".." not in normalized.parts


def list_archive_contents(path: Union[str, Path], max_entries: int = 500) -> List[str]:
    """List archive member paths without full extraction."""
    p = Path(path)
    if not p.is_file():
        return []

    names: List[str] = []
    low = p.name.lower()

    try:
        if low.endswith(".zip"):
            with zipfile.ZipFile(p) as zf:
                for info in zf.infolist()[:max_entries]:
                    if not info.is_dir():
                        names.append(info.filename.replace("\\", "/"))
        elif low.endswith((".tar.gz", ".tgz", ".tar")):
            with tarfile.open(p, "r:*") as tf:
                for member in tf.getmembers()[:max_entries]:
                    if member.isfile():
                        names.append(member.name.replace("\\", "/"))
    except (zipfile.BadZipFile, tarfile.TarError, OSError):
        return []

    return names


def extract_archive(
    path: Union[str, Path],
    dest_dir: Union[str, Path],
    *,
    max_files: int = 5000,
) -> List[str]:
    """
    Extract archive to dest_dir with zip-slip prevention.

    Returns list of extracted file paths (relative to dest_dir).
    """
    p = Path(path)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    extracted: List[str] = []
    low = p.name.lower()
    count = 0

    if low.endswith(".zip"):
        with zipfile.ZipFile(p) as zf:
            for info in zf.infolist():
                if count >= max_files:
                    break
                if info.is_dir():
                    continue
                if not _safe_member_name(info.filename):
                    continue
                target = (dest / info.filename).resolve()
                if not str(target).startswith(str(dest.resolve())):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as dst:
                    while chunk := src.read(65536):
                        dst.write(chunk)
                extracted.append(str(target.relative_to(dest)))
                count += 1
    elif low.endswith((".tar.gz", ".tgz", ".tar")):
        with tarfile.open(p, "r:*") as tf:
            for member in tf.getmembers():
                if count >= max_files:
                    break
                if not member.isfile():
                    continue
                if not _safe_member_name(member.name):
                    continue
                target = (dest / member.name).resolve()
                if not str(target).startswith(str(dest.resolve())):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with tf.extractfile(member) as src:
                    if src is None:
                        continue
                    with open(target, "wb") as dst:
                        while chunk := src.read(65536):
                            dst.write(chunk)
                extracted.append(str(target.relative_to(dest)))
                count += 1

    return extracted
