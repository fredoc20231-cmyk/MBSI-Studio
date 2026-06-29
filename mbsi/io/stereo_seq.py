"""STOmics Stereo-seq ingestion — GEF/CGEF, StereoMap/SAW exports, and tabular fallbacks."""

from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.io.converters import normalize_to_contract
from mbsi.io.detect import PlatformDetection
from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad

STEREO_MAP_MARKERS = ("stereomap", "gem.xls", "cell_cut", "tissue_cut")
SAW_MARKERS = ("saw", "visualization", "report.html", "gef")
QC_HTML_MARKERS = ("qc", "report.html", "quality")

FileInput = Union[str, Path, List[str], Dict[str, Any]]


def _normalize_file_list(files: FileInput) -> Tuple[Optional[Path], List[str]]:
    if isinstance(files, dict):
        root = files.get("_root")
        names = [n for n in files.keys() if not n.startswith("_")]
        return (Path(root) if root else None, names)
    if isinstance(files, (str, Path)):
        p = Path(files)
        if p.is_dir():
            rel = [str(f.relative_to(p)).replace("\\", "/") for f in p.rglob("*") if f.is_file()]
            return p, rel
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as zf:
                return p, zf.namelist()
        return p.parent, [p.name]
    return None, [Path(f).name if isinstance(f, str) and "/" not in f else str(f) for f in files]


def _lower_names(names: List[str]) -> List[str]:
    return [n.lower().replace("\\", "/") for n in names]


def _has_any(names: List[str], markers: tuple[str, ...]) -> bool:
    lowered = _lower_names(names)
    return any(any(m in n for m in markers) for n in lowered)


def detect_stereo_seq(files: FileInput) -> PlatformDetection:
    """Detect STOmics Stereo-seq from file names or folder layout."""
    root, names = _normalize_file_list(files)
    required_found: List[str] = []
    optional_found: List[str] = []
    missing: List[str] = []

    lowered = _lower_names(names)
    has_gef = any(n.endswith(".gef") and "cell" not in n for n in lowered)
    has_cgef = any(n.endswith(".cgef") or ("cell" in n and n.endswith(".gef")) for n in lowered)
    has_h5ad = any(n.endswith(".h5ad") for n in lowered)
    has_coords = _has_any(names, ("coordinates.csv", "coords.csv", "spatial.csv", "position", "gem.xls"))
    has_image = _has_any(names, (".tif", ".tiff", ".png", "registered", "tissue_image"))
    has_tissue_seg = _has_any(names, ("tissue", "segmentation", "geojson", "mask"))
    has_cell_seg = _has_any(names, ("cell", "segmentation", "cgef", "cell_mask"))
    has_regions = _has_any(names, ("region", "annotation", "roi"))
    has_stereomap = _has_any(names, STEREO_MAP_MARKERS)
    has_saw = _has_any(names, SAW_MARKERS)
    has_qc = _has_any(names, QC_HTML_MARKERS)

    if has_gef:
        required_found.append("expression_gef")
    if has_cgef:
        required_found.append("expression_cgef")
    if has_h5ad:
        required_found.append("h5ad_export")
    if has_coords:
        required_found.append("coordinates")
    if has_image:
        optional_found.append("registered_image")
    if has_tissue_seg:
        optional_found.append("tissue_segmentation")
    if has_cell_seg:
        optional_found.append("cell_segmentation")
    if has_regions:
        optional_found.append("region_annotations")
    if has_stereomap:
        optional_found.append("stereomap_outputs")
    if has_saw:
        optional_found.append("saw_outputs")
    if has_qc:
        optional_found.append("qc_report")

    is_stereo = has_gef or has_cgef or (has_saw and (has_h5ad or has_coords))
    if not is_stereo and has_h5ad and _has_any(names, ("stereo", "stomics", "saw")):
        is_stereo = True
        required_found.append("h5ad_stereo_tagged")

    if not is_stereo:
        return {
            "platform": "unknown",
            "required_found": required_found,
            "optional_found": optional_found,
            "missing": ["stereo_seq_signature_files"],
            "confidence": 0.0,
            "root": str(root) if root else None,
            "n_files": len(names),
        }

    if not has_gef and not has_cgef and not has_h5ad:
        missing.append("expression_matrix (GEF/CGEF or SAW h5ad)")
    if not has_coords and not has_h5ad:
        missing.append("coordinates")

    confidence = 0.5
    if has_gef or has_cgef:
        confidence += 0.2
    if has_coords or has_h5ad:
        confidence += 0.15
    if has_saw or has_stereomap:
        confidence += 0.1
    if has_cell_seg or has_tissue_seg:
        confidence += 0.05
    confidence = min(confidence, 0.98)

    return {
        "platform": "stereo_seq",
        "required_found": required_found,
        "optional_found": optional_found,
        "missing": missing,
        "confidence": confidence,
        "root": str(root) if root else None,
        "n_files": len(names),
        "resolution_class": "ultra_high",
    }


def detect_stereo_seq_assets(path_or_files: Union[str, Path, List[str]]) -> Dict[str, Any]:
    """Backward-compatible asset detection wrapper."""
    detection = detect_stereo_seq(path_or_files)
    root, names = _normalize_file_list(path_or_files if not isinstance(path_or_files, list) else path_or_files)
    lowered = _lower_names(names if isinstance(path_or_files, list) else names)
    assets = {
        "gef": any(n.endswith(".gef") for n in lowered),
        "cgef": any(n.endswith(".cgef") for n in lowered),
        "registered_images": _has_any(names, (".tif", "registered", "tissue_image")),
        "segmentation": _has_any(names, ("segmentation", "cell_mask", "tissue_mask")),
        "clustering_outputs": _has_any(names, ("cluster", "umap", "leiden")),
        "lasso_regions": _has_any(names, ("lasso", "region", "roi")),
        "html_qc_report": _has_any(names, QC_HTML_MARKERS),
        "saw_stereomap": _has_any(names, SAW_MARKERS + STEREO_MAP_MARKERS),
    }
    return {
        "platform": "stereo_seq",
        "detection": detection,
        "assets": assets,
        "partial_support": True,
        "message": "Stereo-seq detection complete; GEF/CGEF full parse may be limited",
    }


def _parse_qc_html(path: Path) -> Dict[str, Any]:
    """Partial HTML QC parse — extract numeric metrics from report text."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"parsed": False, "error": "unreadable"}
    metrics: Dict[str, Any] = {"parsed": True, "source": str(path.name)}
    for pattern, key in (
        (r"gene\s*saturation[:\s]*([\d.]+)", "gene_saturation"),
        (r"bin\s*density[:\s]*([\d.]+)", "bin_density"),
        (r"total\s*genes[:\s]*([\d,]+)", "total_genes"),
        (r"total\s*bins[:\s]*([\d,]+)", "total_bins"),
        (r"cell\s*count[:\s]*([\d,]+)", "cell_count"),
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", "")
            metrics[key] = float(val) if "." in val else int(val)
    metrics["snippet_length"] = len(text)
    return metrics


def load_stereo_qc_html(path: Union[str, Path]) -> Dict[str, Any]:
    """Load Stereo-seq HTML QC report metadata (partial parse)."""
    path = Path(path)
    html_files = list(path.rglob("*.html")) if path.is_dir() else ([path] if path.suffix.lower() == ".html" else [])
    qc_reports = [p for p in html_files if "qc" in p.name.lower() or "report" in p.name.lower()]
    if not qc_reports:
        return {"found": False, "message": "No StereoMap HTML QC report found"}
    parsed = _parse_qc_html(qc_reports[0])
    return {
        "found": True,
        "path": str(qc_reports[0]),
        "partial_support": True,
        "metrics": parsed,
        "message": "HTML QC report detected; partial metric extraction only",
    }


def _try_h5py_attrs(path: Path) -> Dict[str, Any]:
    """Read GEF/CGEF HDF5 header metadata when h5py is available."""
    meta: Dict[str, Any] = {"path": str(path), "format": path.suffix.lower()}
    try:
        import h5py
    except ImportError:
        meta["note"] = "h5py not installed — GEF/CGEF expression not parsed"
        meta["parsed"] = False
        return meta
    try:
        with h5py.File(path, "r") as f:
            meta["parsed"] = True
            meta["keys"] = list(f.keys())[:20]
            for attr_key in ("version", "binSize", "bin_size", "resolution"):
                if attr_key in f.attrs:
                    meta[attr_key] = f.attrs[attr_key]
    except OSError as exc:
        meta["parsed"] = False
        meta["error"] = str(exc)
        meta["note"] = "GEF/CGEF binary parse limited — use SAW h5ad export for full load"
    return meta


def load_gef(path: Union[str, Path]) -> Dict[str, Any]:
    """Load GEF bin-level expression metadata (full binary parse not guaranteed)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    return _try_h5py_attrs(path)


def load_cgef(path: Union[str, Path]) -> Dict[str, Any]:
    """Load CGEF cell-level expression metadata (full binary parse not guaranteed)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    meta = _try_h5py_attrs(path)
    meta["level"] = "cell"
    return meta


def load_stereo_map_outputs(path: Union[str, Path]) -> Dict[str, Any]:
    """Index StereoMap export folder — gem.xls, cut files, QC sidecars."""
    root = Path(path)
    if not root.is_dir():
        raise NotADirectoryError(path)
    files = [f for f in root.rglob("*") if f.is_file()]
    names = [str(f.relative_to(root)) for f in files]
    out: Dict[str, Any] = {"source": str(root), "n_files": len(files), "files": names[:50]}
    gem = next((f for f in files if f.name.lower().endswith("gem.xls") or f.name.lower() == "gem.xls"), None)
    if gem is not None:
        out["gem_xls"] = str(gem)
    coords_csv = next((f for f in files if "coord" in f.name.lower() and f.suffix == ".csv"), None)
    if coords_csv is not None:
        out["coordinates_csv"] = str(coords_csv)
    return out


def load_saw_outputs(path: Union[str, Path]) -> Dict[str, Any]:
    """Index SAW pipeline outputs — prefer h5ad and coordinate exports."""
    root = Path(path)
    if not root.is_dir():
        raise NotADirectoryError(path)
    files = [f for f in root.rglob("*") if f.is_file()]
    out: Dict[str, Any] = {"source": str(root), "n_files": len(files)}
    h5ad_files = [f for f in files if f.suffix.lower() == ".h5ad"]
    gef_files = [f for f in files if f.suffix.lower() in (".gef", ".cgef")]
    html_reports = [f for f in files if f.suffix.lower() in (".html", ".htm")]
    if h5ad_files:
        out["h5ad"] = str(h5ad_files[0])
    if gef_files:
        out["gef"] = str(gef_files[0])
    if html_reports:
        out["qc_reports"] = [str(p) for p in html_reports[:5]]
        out["qc_parsed"] = [_parse_qc_html(p) for p in html_reports[:3]]
    return out


def _resolve_root(path: Union[str, Path]) -> Tuple[Path, Optional[Path]]:
    """Return data root and optional temp dir."""
    path = Path(path)
    if path.is_dir():
        return path, None
    if path.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="mbsi_stereo_"))
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        return tmp, tmp
    if path.is_file() and path.suffix.lower() in (".gef", ".cgef", ".h5ad"):
        return path.parent, None
    raise FileNotFoundError(f"Not a Stereo-seq directory, ZIP, or file: {path}")


def _find_file(root: Path, patterns: tuple[str, ...]) -> Optional[Path]:
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        name = f.name.lower()
        rel = str(f.relative_to(root)).lower()
        if any(p in name or p in rel for p in patterns):
            return f
    return None


def _load_coords_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    if "x" in cols and "y" in cols:
        return df.rename(columns={cols["x"]: "x", cols["y"]: "y"})
    for xc, yc in (("x_coord", "y_coord"), ("X", "Y"), ("col", "row")):
        if xc.lower() in cols and yc.lower() in cols:
            return df.rename(columns={cols[xc.lower()]: "x", cols[yc.lower()]: "y"})
    if df.shape[1] >= 2:
        df = df.copy()
        df.columns = list(df.columns[: df.shape[1] - 2]) + ["x", "y"]
        return df
    raise ValueError(f"Could not infer x/y columns in {path}")


def _load_expression_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".csv", ".tsv", ".txt"):
        sep = "\t" if path.suffix.lower() in (".tsv", ".txt") else ","
        return pd.read_csv(path, sep=sep, index_col=0)
    if path.suffix.lower() in (".xls", ".xlsx"):
        return pd.read_excel(path, index_col=0)
    raise ValueError(f"Unsupported expression table: {path}")


def convert_to_anndata(
    expression: Optional[pd.DataFrame] = None,
    coordinates: Optional[pd.DataFrame] = None,
    *,
    platform: str = "stereo_seq",
    scale: str = "bin",
    stereo_meta: Optional[Dict[str, Any]] = None,
    detection: Optional[PlatformDetection] = None,
) -> ad.AnnData:
    """Build AnnData from tabular Stereo-seq components."""
    if expression is None:
        raise ValueError("expression matrix required for AnnData conversion")
    X = expression.values.astype(np.float32)
    adata = ad.AnnData(X=X)
    adata.obs_names = expression.index.astype(str)
    adata.var_names = expression.columns.astype(str)

    if coordinates is not None:
        if len(coordinates) == adata.n_obs:
            adata.obs["x"] = coordinates["x"].values
            adata.obs["y"] = coordinates["y"].values
        elif "x" in coordinates.columns and "y" in coordinates.columns:
            adata.obs["x"] = coordinates["x"].values[: adata.n_obs]
            adata.obs["y"] = coordinates["y"].values[: adata.n_obs]
        adata.obsm["spatial"] = adata.obs[["x", "y"]].values.astype(np.float32)

    adata.obs["stereo_scale"] = scale
    if stereo_meta:
        adata.uns["stereo_seq"] = stereo_meta
    return normalize_to_contract(adata, platform=platform, detection=detection)


def compute_stereo_seq_readiness(
    adata: ad.AnnData,
    detection: Optional[PlatformDetection] = None,
    stereo_assets: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Stereo-seq-specific readiness beyond generic contract."""
    from mbsi.io.validators import compute_readiness

    score, details = compute_readiness(adata, detection)
    checks = details.setdefault("checks", {})
    assets = stereo_assets or adata.uns.get("stereo_seq", {})

    if adata.uns.get("stereo_seq", {}).get("gef") or assets.get("gef"):
        checks["gef_present"] = True
        score = min(100, score + 5)
    if adata.uns.get("stereo_seq", {}).get("cgef") or assets.get("cgef"):
        checks["cgef_present"] = True
        score = min(100, score + 5)
    if "cell_id" in adata.obs or adata.obs.get("stereo_scale", pd.Series()).eq("cell").any():
        checks["cell_level"] = True
        score = min(100, score + 5)
    if "region_id" in adata.obs or assets.get("regions"):
        checks["regions"] = True
        score = min(100, score + 5)
    if assets.get("segmentation") or "segmentation" in adata.uns:
        checks["segmentation"] = True
        score = min(100, score + 5)
    if assets.get("registered_image") or adata.uns.get("spatial"):
        checks["histology"] = True

    n_obs = adata.n_obs
    if n_obs >= 1000:
        checks["ultra_high_resolution"] = True
    elif n_obs >= 100:
        checks["high_resolution"] = True

    if score >= 85:
        details["status"] = "Ready for ultra-high-resolution analysis"
    details["score"] = score
    details["platform"] = "stereo_seq"
    details["stereo_assets"] = {k: bool(v) for k, v in (assets or {}).items()}
    return score, details


def load_stereo_seq_dataset(files: Union[str, Path, List[str]]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """
    Load Stereo-seq dataset from folder or ZIP.

    Priority: SAW h5ad → CSV matrix+coords → GEF/CGEF metadata-only stub with synthetic grid if needed.
    """
    tmp: Optional[Path] = None
    if isinstance(files, list):
        raise ValueError("load_stereo_seq_dataset requires a directory or ZIP path, not a bare file list")

    root, tmp = _resolve_root(files)
    try:
        if root.is_dir():
            names = [str(f.relative_to(root)).replace("\\", "/") for f in root.rglob("*") if f.is_file()]
        else:
            names = [root.name]
        detection = detect_stereo_seq({"_root": str(root), **{n: True for n in names}})

        data_root = root
        stereo_meta: Dict[str, Any] = {"detection": detection, "limitations": []}
        adata: Optional[ad.AnnData] = None

        saw_dir = _find_file(data_root, ("saw", "visualization"))
        if saw_dir and saw_dir.is_dir():
            saw_info = load_saw_outputs(saw_dir)
            stereo_meta["saw"] = saw_info
            if saw_info.get("h5ad"):
                adata, h5_meta = ingest_h5ad(saw_info["h5ad"])
                stereo_meta["source"] = "saw_h5ad"
                stereo_meta.update(h5_meta)

        if adata is None:
            h5ad_path = _find_file(data_root, (".h5ad",))
            if h5ad_path is not None:
                adata, h5_meta = ingest_h5ad(h5ad_path)
                stereo_meta["source"] = "h5ad"
                stereo_meta.update(h5_meta)

        coords_path = _find_file(data_root, ("coordinates.csv", "coords.csv", "spatial.csv", "position"))
        matrix_path = _find_file(data_root, ("matrix.csv", "counts.csv", "expression.csv", "gem.xls"))

        if adata is None and matrix_path is not None and coords_path is not None:
            matrix = _load_expression_table(matrix_path)
            coords = _load_coords_csv(coords_path)
            adata = convert_to_anndata(matrix, coords, stereo_meta={"source": "csv_matrix_coords"})
            stereo_meta["source"] = "csv_matrix_coords"

        gef_path = _find_file(data_root, (".gef",))
        cgef_path = _find_file(data_root, (".cgef", "cell.bin.gef"))
        if gef_path is not None:
            stereo_meta["gef"] = load_gef(gef_path)
        if cgef_path is not None:
            stereo_meta["cgef"] = load_cgef(cgef_path)

        if adata is None and (gef_path or cgef_path):
            stereo_meta["limitations"].append(
                "GEF/CGEF binary expression not fully parsed — provide SAW h5ad or CSV matrix + coordinates"
            )
            n_bins = 64
            rng = np.random.default_rng(42)
            genes = [f"Gene{i}" for i in range(50)]
            coords_df = pd.DataFrame({"x": rng.uniform(0, 1000, n_bins), "y": rng.uniform(0, 1000, n_bins)})
            expr = pd.DataFrame(
                rng.poisson(3, (n_bins, len(genes))).astype(float),
                index=[f"bin{i}" for i in range(n_bins)],
                columns=genes,
            )
            adata = convert_to_anndata(expr, coords_df, scale="bin", stereo_meta=stereo_meta, detection=detection)
            adata.uns["stereo_seq_placeholder"] = True
            stereo_meta["source"] = "gef_stub"

        stereomap_dir = _find_file(data_root, ("stereomap",))
        if stereomap_dir is not None and stereomap_dir.is_dir():
            stereo_meta["stereomap"] = load_stereo_map_outputs(stereomap_dir)

        qc_html = _find_file(data_root, ("qc", "report.html", "quality"))
        if qc_html is not None and qc_html.suffix.lower() in (".html", ".htm"):
            stereo_meta["qc_report"] = _parse_qc_html(qc_html)

        seg_path = _find_file(data_root, ("segmentation", "cell_mask", "tissue_mask"))
        if seg_path is not None:
            stereo_meta["segmentation"] = str(seg_path)

        img_path = _find_file(data_root, ("registered", "tissue_image", ".tif"))
        if img_path is not None:
            stereo_meta["registered_image"] = str(img_path)

        region_path = _find_file(data_root, ("region", "annotation", "roi"))
        if region_path is not None and region_path.suffix.lower() == ".csv":
            try:
                regions = pd.read_csv(region_path)
                stereo_meta["regions"] = True
                if adata is not None and "region_id" not in adata.obs and len(regions) == adata.n_obs:
                    id_col = next(
                        (c for c in regions.columns if "region" in c.lower() or "roi" in c.lower()),
                        regions.columns[0],
                    )
                    adata.obs["region_id"] = regions[id_col].astype(str).values
            except Exception:
                pass

        if adata is None:
            raise ValueError("Could not load Stereo-seq dataset — no h5ad, CSV matrix+coords, or GEF sidecars found")

        adata.uns["stereo_seq"] = stereo_meta
        adata.uns["mbsi_platform"] = "stereo_seq"
        if "spatial" not in adata.obsm and "x" in adata.obs and "y" in adata.obs:
            adata.obsm["spatial"] = adata.obs[["x", "y"]].values.astype(np.float32)

        score, readiness = compute_stereo_seq_readiness(adata, detection, stereo_meta)
        adata.uns["mbsi_readiness"] = readiness
        adata.uns["mbsi_readiness_score"] = score

        return adata, {
            "platform": "stereo_seq",
            "detection": detection,
            "readiness_score": score,
            "readiness": readiness,
            "stereo_seq_readiness": readiness,
            "stereo_seq": stereo_meta,
            "source": str(files),
            "limitations": stereo_meta.get("limitations", []),
        }
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


def load_stereo_seq(path: Union[str, Path]) -> Tuple[ad.AnnData, Dict[str, Any]]:
    """Alias for load_stereo_seq_dataset."""
    return load_stereo_seq_dataset(path)
