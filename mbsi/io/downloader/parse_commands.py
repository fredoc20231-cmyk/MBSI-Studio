"""Parse curl/wget commands and raw URL lists — no shell execution."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]+",
    re.IGNORECASE,
)

_CURL_O_RE = re.compile(
    r"curl\b[^\n]*?(?:-O|--remote-name)\b[^\n]*?(https?://[^\s\"']+)",
    re.IGNORECASE,
)
_CURL_OUT_RE = re.compile(
    r"curl\b[^\n]*?(?:-o|--output)\s+(\S+)\s+(https?://[^\s\"']+)",
    re.IGNORECASE,
)
_CURL_URL_RE = re.compile(
    r"curl\b[^\n]*?(https?://[^\s\"']+)",
    re.IGNORECASE,
)
_WGET_O_RE = re.compile(
    r"wget\b[^\n]*?(?:-O|--output-document=)\s*(\S+)\s+(https?://[^\s\"']+)",
    re.IGNORECASE,
)
_WGET_URL_RE = re.compile(
    r"wget\b[^\n]*?(https?://[^\s\"']+)",
    re.IGNORECASE,
)

_10X_HOSTS = ("10xgenomics.com", "cf.10xgenomics.com", "support.10xgenomics.com")
_STOMICS_HOSTS = ("stomics.tech", "stomics.com", "genomics.cn", "bgitech")
_VIZGEN_HOSTS = ("vizgen.com", "vizgen.io")
_COSMX_HOSTS = ("nanostring.com", "cosmx", "brb-seq.com")


def _sanitize_filename(name: str) -> str:
    name = unquote(name).strip().replace("\\", "/")
    name = Path(name).name
    name = re.sub(r"[^\w.\-()+ ]", "_", name)
    return name or "download.bin"


def infer_filename_from_url(url: str) -> str:
    """Derive a safe local filename from a URL path."""
    parsed = urlparse(url.strip())
    path = unquote(parsed.path.rstrip("/"))
    if path:
        candidate = Path(path).name
        if candidate and candidate not in (".", "/"):
            return _sanitize_filename(candidate)
    if parsed.query:
        for part in parsed.query.split("&"):
            if "=" in part:
                _, val = part.split("=", 1)
                if val and "." in val:
                    return _sanitize_filename(val)
    return "download.bin"


def _infer_source_from_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if any(h in host for h in _10X_HOSTS):
        return "10x"
    if any(h in host for h in _STOMICS_HOSTS):
        return "stomics"
    if any(h in host for h in _VIZGEN_HOSTS):
        return "vizgen"
    if any(h in host for h in _COSMX_HOSTS):
        return "cosmx"
    return "generic"


def _classify_filename(filename: str, source: str) -> tuple[str, str]:
    """Return (likely_role, technology_hint) from filename."""
    low = filename.lower()

    if low.endswith("_xe_outs.zip") or "_xe_outs" in low:
        return "xenium_explorer_archive", "xenium"
    if low.endswith("_outs.zip") or re.search(r"_outs\.zip$", low):
        return "output_archive", "xenium"
    if low.endswith(".zip") and any(k in low for k in ("visium", "spaceranger", "space_ranger")):
        return "visium_archive", "visium"
    if low.endswith(".zip") and any(k in low for k in ("xenium", "cell_feature")):
        return "xenium_archive", "xenium"
    if low.endswith(".zip") and any(k in low for k in ("merfish", "merscope", "vizgen")):
        return "merfish_archive", "merfish"
    if low.endswith(".zip") and "cosmx" in low:
        return "cosmx_archive", "cosmx"
    if low.endswith(".zip") and any(k in low for k in ("stereo", "stomics", "gef", "saw")):
        return "stereo_seq_archive", "stereo_seq"
    if low.endswith(".zip"):
        return "archive", "unknown"

    if low in ("gene_groups.csv", "cell_groups.csv") or low.endswith("gene_groups.csv"):
        return "metadata_groups", "xenium"
    if low.endswith("cell_groups.csv"):
        return "metadata_groups", "xenium"
    if low.endswith(".ome.tif") or low.endswith(".ome.tiff") or "he_image" in low:
        return "histology_image", "xenium"
    if "he_alignment" in low or low.endswith("alignment.csv"):
        return "registration", "xenium"
    if "keypoints" in low:
        return "registration", "xenium"
    if low.endswith(".h5ad"):
        return "expression_matrix", "generic_h5ad"
    if low.endswith(".gef") or low.endswith(".cgef"):
        return "expression_matrix", "stereo_seq"
    if "tissue_positions" in low:
        return "spatial_coordinates", "visium"
    if "filtered_feature_bc_matrix" in low or low.endswith(".h5"):
        return "count_matrix", "visium"
    if "cells.csv" in low or "cells.parquet" in low:
        return "cell_metadata", "xenium"
    if "exprmat" in low or "fov_positions" in low:
        return "expression_matrix", "cosmx"
    if "cell_by_gene" in low:
        return "expression_matrix", "merfish"

    if source == "10x":
        return "supplementary", "xenium"
    if source == "stomics":
        return "supplementary", "stereo_seq"
    if source == "vizgen":
        return "supplementary", "merfish"
    if source == "cosmx":
        return "supplementary", "cosmx"
    return "unknown", "unknown"


def classify_download_url(url: str, filename: str | None = None) -> dict:
    """Classify a download URL by source, role, and technology hint."""
    fname = filename or infer_filename_from_url(url)
    source = _infer_source_from_url(url)
    role, tech = _classify_filename(fname, source)
    return {
        "url": url.strip(),
        "filename": fname,
        "source": source,
        "likely_role": role,
        "technology_hint": tech,
    }


def extract_urls_from_text(text: str) -> list[str]:
    """
    Extract URLs from curl/wget commands or plain URL lists.

    Supports: curl -O URL, curl -L -o filename URL, wget URL, wget -O filename URL,
    and raw URLs (one per line or embedded in text). Does NOT execute shell commands.
    """
    if not text or not text.strip():
        return []

    found: list[str] = []
    seen: set[str] = set()

    def _add(url: str) -> None:
        url = url.strip().rstrip(")'\",;")
        if url and url not in seen:
            seen.add(url)
            found.append(url)

    for m in _CURL_OUT_RE.finditer(text):
        _add(m.group(2))
    for m in _CURL_O_RE.finditer(text):
        _add(m.group(1))
    for m in _WGET_O_RE.finditer(text):
        _add(m.group(2))
    for m in _WGET_URL_RE.finditer(text):
        _add(m.group(1))
    for m in _CURL_URL_RE.finditer(text):
        _add(m.group(1))
    for m in _URL_RE.finditer(text):
        _add(m.group(0))

    return found


def parse_url_entries(text: str) -> list[dict]:
    """Extract URLs and return classified entries with optional curl -o filenames."""
    entries: list[dict] = []
    seen: set[str] = set()

    for m in _CURL_OUT_RE.finditer(text):
        fname, url = m.group(1), m.group(2).strip().rstrip(")'\",;")
        if url in seen:
            continue
        seen.add(url)
        info = classify_download_url(url, fname)
        entries.append(info)

    for m in _WGET_O_RE.finditer(text):
        fname, url = m.group(1), m.group(2).strip().rstrip(")'\",;")
        if url in seen:
            continue
        seen.add(url)
        info = classify_download_url(url, fname)
        entries.append(info)

    for url in extract_urls_from_text(text):
        if url in seen:
            continue
        seen.add(url)
        entries.append(classify_download_url(url))

    return entries
