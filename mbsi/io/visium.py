"""10x Visium / Space Ranger ingestion — Phase 1 full implementation."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import anndata as ad

from mbsi.analysis.visium import read_visium_spaceranger
from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import detect_platform
from mbsi.io.validators import compute_readiness


def _resolve_outs_dir(path: Union[str, Path]) -> tuple[Path, Path | None]:
    """Return outs directory and optional temp dir to clean up."""
    path = Path(path)
    if path.is_dir():
        if (path / "spatial").exists() or (path / "filtered_feature_bc_matrix.h5").exists():
            return path, None
        for sub in ("outs", "spaceranger", "space_ranger"):
            candidate = path / sub
            if candidate.is_dir():
                return candidate, None
        return path, None

    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_visium_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        for h5 in tmp.rglob("filtered_feature_bc_matrix.h5"):
            return h5.parent, tmp
        for positions in tmp.rglob("tissue_positions*.csv"):
            return positions.parent.parent, tmp
        return tmp, tmp

    raise FileNotFoundError(f"Not a Visium outs directory or ZIP: {path}")


def load_space_ranger(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Load Space Ranger outs from directory or ZIP; return AnnData + metadata."""
    outs_dir, tmp = _resolve_outs_dir(path)
    try:
        adata = read_visium_spaceranger(str(outs_dir))
        detection = detect_platform(outs_dir)
        adata = normalize_to_contract(adata, platform="visium", detection=detection)
        score, readiness = compute_readiness(adata, detection)
        meta = {
            "platform": "visium",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "source": str(path),
        }
        return adata, meta
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
