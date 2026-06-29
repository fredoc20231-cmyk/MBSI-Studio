"""Unified ingestion entry points for SaaS upload."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ad
import pandas as pd

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad
from mbsi.io.visium import load_space_ranger


def ingest_upload(
    *,
    h5ad_path: Optional[Path] = None,
    visium_path: Optional[Path] = None,
    count_matrix: Optional[pd.DataFrame] = None,
    coordinates: Optional[pd.DataFrame] = None,
    file_names: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Ingest uploaded files into AnnData + metadata bundle for session_state.

    Returns dict with keys: adata, detection, readiness_score, readiness, compatibility, platform
    """
    detection = detect_platform(file_names or [])
    adata: Optional[ad.AnnData] = None
    meta: Dict[str, Any] = {}

    if visium_path is not None:
        adata, meta = load_space_ranger(visium_path)
        detection = meta.get("detection", detection)
    elif h5ad_path is not None:
        adata, meta = ingest_h5ad(h5ad_path)
        detection = meta.get("detection", detection)
    elif count_matrix is not None and coordinates is not None:
        adata, meta = ingest_csv_matrix_coords(count_matrix, coordinates)
        detection = meta.get("detection", detection)
    else:
        return {
            "adata": None,
            "detection": detection,
            "readiness_score": 0,
            "readiness": {"status": "No ingestible files"},
            "compatibility": get_compatibility_matrix(None, detection),
            "platform": detection.get("platform", "unknown"),
        }

    platform = meta.get("platform", detection.get("platform", "unknown"))
    score = meta.get("readiness_score", adata.uns.get("mbsi_readiness_score", 0))
    readiness = meta.get("readiness", adata.uns.get("mbsi_readiness", {}))
    compatibility = get_compatibility_matrix(adata, detection)

    return {
        "adata": adata,
        "detection": detection,
        "readiness_score": score,
        "readiness": readiness,
        "compatibility": compatibility,
        "platform": platform,
        "source": meta.get("source"),
    }


def save_upload_to_temp(uploaded_file, suffix: str) -> Path:
    """Write Streamlit UploadedFile to temp path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded_file.getbuffer())
        return Path(f.name)
