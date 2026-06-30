"""Universal dataset ingestion — single entry point for all platforms."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import pandas as pd

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad
from mbsi.io.ingest import normalize_loader_result
from mbsi.io.visium import load_space_ranger
from mbsi.schema.technology import get_technology
from mbsi.schema.technology_profile import TechnologyProfile


_REGISTRY_ROOT = Path("data/registry/ingested")


@dataclass
class IngestionResult:
    adata_path: str = ""
    platform: str = "unknown"
    technology_profile: Dict[str, Any] = field(default_factory=dict)
    readiness: Dict[str, Any] = field(default_factory=dict)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    dataset_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adata_path": self.adata_path,
            "platform": self.platform,
            "technology_profile": dict(self.technology_profile),
            "readiness": dict(self.readiness),
            "compatibility": dict(self.compatibility),
            "warnings": list(self.warnings),
            "dataset_id": self.dataset_id,
            "metadata": dict(self.metadata),
        }


def _persist_adata(adata, source: Path, dataset_id: str) -> str:
    if adata is None:
        return ""
    out_dir = _REGISTRY_ROOT / dataset_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "dataset.h5ad"
    adata.write_h5ad(out_path)
    return str(out_path.resolve())


def _stub_result(
    platform: str,
    warnings: List[str],
    *,
    technology_hint: Optional[str] = None,
    dataset_id: Optional[str] = None,
) -> IngestionResult:
    tech_key = technology_hint or platform
    profile = TechnologyProfile.from_technology(tech_key, dataset_id=dataset_id or "")
    detection = detect_platform([platform])
    detection["platform"] = platform
    return IngestionResult(
        adata_path="",
        platform=platform,
        technology_profile=profile.to_dict(),
        readiness={"status": "stub", "score": 0},
        compatibility=get_compatibility_matrix(None, detection, tech_key),
        warnings=warnings,
        dataset_id=dataset_id or str(uuid4()),
        metadata={"detection": detection, "source": platform},
    )


def _ingest_platform_loader(
    loader_name: str,
    path: Path,
    *,
    dataset_id: str,
    technology_hint: Optional[str],
) -> IngestionResult:
    warnings: List[str] = []
    adata = None
    meta: Dict[str, Any] = {}

    try:
        if loader_name == "xenium":
            from mbsi.io.xenium import load_xenium

            adata, meta = load_xenium(path)
        elif loader_name == "merfish":
            from mbsi.io.merfish import load_merfish

            adata, meta = load_merfish(path)
        elif loader_name == "cosmx":
            from mbsi.io.cosmx import load_cosmx

            adata, meta = load_cosmx(path)
        elif loader_name == "codex":
            from mbsi.io.codex import load_codex

            adata, meta = load_codex(path)
        elif loader_name == "stereo_seq":
            from mbsi.io.stereo_seq import load_stereo_seq_dataset

            adata, meta = load_stereo_seq_dataset(path)
        elif loader_name == "spatial_atac":
            from mbsi.io.spatial_atac import load_spatial_atac

            adata, meta = load_spatial_atac(path)
        else:
            return _stub_result(
                loader_name,
                [f"No loader registered for platform: {loader_name}"],
                technology_hint=technology_hint,
                dataset_id=dataset_id,
            )
    except NotImplementedError as exc:
        return _stub_result(
            loader_name,
            [str(exc)],
            technology_hint=technology_hint,
            dataset_id=dataset_id,
        )
    except Exception as exc:
        warnings.append(f"{loader_name} loader failed: {exc}")
        return IngestionResult(
            adata_path="",
            platform=loader_name,
            technology_profile=TechnologyProfile.from_technology(
                technology_hint or loader_name, dataset_id=dataset_id
            ).to_dict(),
            readiness={"status": "error", "score": 0},
            compatibility=get_compatibility_matrix(None),
            warnings=warnings,
            dataset_id=dataset_id,
            metadata={"source": str(path)},
        )

    if meta.get("note"):
        warnings.append(str(meta["note"]))
    if meta.get("limitations"):
        warnings.extend(meta["limitations"])

    normalized = normalize_loader_result(
        {
            "adata": adata,
            "platform": meta.get("platform", loader_name),
            "detection": meta.get("detection", {}),
            "readiness": meta.get("readiness", {}),
            "readiness_score": meta.get("readiness_score", 0),
            "compatibility": meta.get("compatibility"),
            "warnings": warnings,
            "metadata": meta,
            "source": str(path),
        }
    )
    adata_path = _persist_adata(normalized.get("adata"), path, dataset_id)
    tech_key = technology_hint or normalized.get("platform", loader_name)
    profile = TechnologyProfile.from_technology(tech_key, dataset_id=dataset_id)
    return IngestionResult(
        adata_path=adata_path,
        platform=str(normalized.get("platform", loader_name)),
        technology_profile=profile.to_dict(),
        readiness=dict(normalized.get("readiness") or {}),
        compatibility=dict(normalized.get("compatibility") or {}),
        warnings=list(normalized.get("warnings") or []),
        dataset_id=dataset_id,
        metadata={
            "detection": normalized.get("detection", {}),
            "source": str(path),
            "n_obs": int(adata.n_obs) if adata is not None else 0,
            "n_vars": int(adata.n_vars) if adata is not None else 0,
        },
    )


def _resolve_source_path(source: Union[str, Path]) -> Path:
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Source not found: {path}")
    return path


def _ingest_h5ad(path: Path, *, dataset_id: str, technology_hint: Optional[str]) -> IngestionResult:
    adata, meta = ingest_h5ad(path)
    normalized = normalize_loader_result(
        {
            "adata": adata,
            "platform": meta.get("platform", "generic_h5ad"),
            "detection": meta.get("detection", {}),
            "readiness": meta.get("readiness", {}),
            "readiness_score": meta.get("readiness_score", 0),
            "source": str(path),
        }
    )
    adata_path = _persist_adata(adata, path, dataset_id)
    tech_key = technology_hint or normalized.get("platform", "generic_h5ad")
    return IngestionResult(
        adata_path=adata_path,
        platform=str(normalized.get("platform", "generic_h5ad")),
        technology_profile=TechnologyProfile.from_technology(tech_key, dataset_id=dataset_id).to_dict(),
        readiness=dict(normalized.get("readiness") or {}),
        compatibility=dict(normalized.get("compatibility") or {}),
        warnings=list(normalized.get("warnings") or []),
        dataset_id=dataset_id,
        metadata={
            "detection": normalized.get("detection", {}),
            "source": str(path),
            "n_obs": int(adata.n_obs),
            "n_vars": int(adata.n_vars),
        },
    )


def _ingest_csv_pair(path: Path, *, dataset_id: str) -> IngestionResult:
    parent = path.parent
    matrix_path = path
    coords_path = parent / "coordinates.csv"
    if not coords_path.exists():
        for candidate in parent.glob("*coord*.csv"):
            coords_path = candidate
            break
    if not coords_path.exists():
        return IngestionResult(
            adata_path="",
            platform="csv_matrix",
            technology_profile=TechnologyProfile.from_technology("generic_h5ad", dataset_id=dataset_id).to_dict(),
            readiness={"status": "missing_coords", "score": 0},
            compatibility=get_compatibility_matrix(None),
            warnings=["CSV matrix found but coordinates.csv missing"],
            dataset_id=dataset_id,
            metadata={"source": str(path)},
        )
    matrix = pd.read_csv(matrix_path, index_col=0)
    coords = pd.read_csv(coords_path)
    adata, meta = ingest_csv_matrix_coords(matrix, coords)
    normalized = normalize_loader_result(
        {
            "adata": adata,
            "platform": "csv_matrix",
            "detection": meta.get("detection", {}),
            "readiness": meta.get("readiness", {}),
            "readiness_score": meta.get("readiness_score", 0),
            "source": str(path),
        }
    )
    adata_path = _persist_adata(adata, path, dataset_id)
    return IngestionResult(
        adata_path=adata_path,
        platform="csv_matrix",
        technology_profile=TechnologyProfile.from_technology("generic_h5ad", dataset_id=dataset_id).to_dict(),
        readiness=dict(normalized.get("readiness") or {}),
        compatibility=dict(normalized.get("compatibility") or {}),
        warnings=list(normalized.get("warnings") or []),
        dataset_id=dataset_id,
        metadata={
            "detection": normalized.get("detection", {}),
            "source": str(path),
            "n_obs": int(adata.n_obs),
            "n_vars": int(adata.n_vars),
        },
    )


def _ingest_visium_zip(path: Path, *, dataset_id: str) -> IngestionResult:
    extract_dir = Path(tempfile.mkdtemp(prefix="mbsi_visium_"))
    warnings: List[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            zf.extractall(extract_dir)
        adata, meta = load_space_ranger(extract_dir)
        normalized = normalize_loader_result(
            {
                "adata": adata,
                "platform": meta.get("platform", "visium"),
                "detection": meta.get("detection", {}),
                "readiness": meta.get("readiness", {}),
                "readiness_score": meta.get("readiness_score", 0),
                "source": str(path),
            }
        )
        adata_path = _persist_adata(adata, path, dataset_id)
        return IngestionResult(
            adata_path=adata_path,
            platform="visium",
            technology_profile=TechnologyProfile.from_technology("visium", dataset_id=dataset_id).to_dict(),
            readiness=dict(normalized.get("readiness") or {}),
            compatibility=dict(normalized.get("compatibility") or {}),
            warnings=list(normalized.get("warnings") or []) + warnings,
            dataset_id=dataset_id,
            metadata={
                "detection": normalized.get("detection", {}),
                "source": str(path),
                "n_obs": int(adata.n_obs),
                "n_vars": int(adata.n_vars),
            },
        )
    except Exception as exc:
        warnings.append(f"Visium ZIP ingest failed: {exc}")
        return IngestionResult(
            adata_path="",
            platform="visium",
            technology_profile=TechnologyProfile.from_technology("visium", dataset_id=dataset_id).to_dict(),
            readiness={"status": "error", "score": 0},
            compatibility=get_compatibility_matrix(None),
            warnings=warnings,
            dataset_id=dataset_id,
            metadata={"source": str(path)},
        )
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def ingest_dataset(
    source: Union[str, Path],
    technology_hint: Optional[str] = None,
    *,
    dataset_id: Optional[str] = None,
) -> IngestionResult:
    """
    Unified ingestion entry — returns JSON-serializable metadata and adata path reference.

    Supports: h5ad, CSV+coords, Visium ZIP, xenium, merfish, cosmx, stereo_seq, codex, spatial_atac.
    Honest stubs return clear warnings when full parsers are unavailable.
    """
    path = _resolve_source_path(source)
    dataset_id = dataset_id or str(uuid4())
    suffix = path.suffix.lower()
    name_lower = path.name.lower()

    platform_loaders = {
        "xenium": "xenium",
        "merfish": "merfish",
        "cosmx": "cosmx",
        "codex": "codex",
        "stereo_seq": "stereo_seq",
        "spatial_atac": "spatial_atac",
    }

    if technology_hint and technology_hint in platform_loaders:
        return _ingest_platform_loader(
            platform_loaders[technology_hint],
            path,
            dataset_id=dataset_id,
            technology_hint=technology_hint,
        )

    if suffix == ".h5ad":
        return _ingest_h5ad(path, dataset_id=dataset_id, technology_hint=technology_hint)

    if suffix == ".csv" and "coord" not in name_lower:
        return _ingest_csv_pair(path, dataset_id=dataset_id)

    if suffix == ".zip" and any(k in name_lower for k in ("visium", "spaceranger", "outs")):
        return _ingest_visium_zip(path, dataset_id=dataset_id)

    if suffix in (".gef", ".cgef") or "stereo" in name_lower:
        return _ingest_platform_loader("stereo_seq", path, dataset_id=dataset_id, technology_hint="stereo_seq")

    detection = detect_platform([path.name])
    detected = technology_hint or detection.get("platform", "unknown")

    if detected in platform_loaders:
        return _ingest_platform_loader(
            platform_loaders[detected],
            path,
            dataset_id=dataset_id,
            technology_hint=detected,
        )

    if path.is_dir():
        for loader in ("visium", "xenium", "merfish", "cosmx", "codex", "stereo_seq", "spatial_atac"):
            try:
                return _ingest_platform_loader(
                    loader,
                    path,
                    dataset_id=dataset_id,
                    technology_hint=technology_hint or loader,
                )
            except Exception:
                continue

    if suffix == ".zip":
        return _ingest_visium_zip(path, dataset_id=dataset_id)

    tech = get_technology(detected)
    return IngestionResult(
        adata_path="",
        platform=str(detected),
        technology_profile=TechnologyProfile.from_technology(
            detected if tech else "generic_h5ad",
            dataset_id=dataset_id,
        ).to_dict(),
        readiness={"status": "unsupported", "score": 0},
        compatibility=get_compatibility_matrix(None, detection, detected),
        warnings=[f"Unsupported or unrecognized source format: {path.name}"],
        dataset_id=dataset_id,
        metadata={"detection": detection, "source": str(path)},
    )
