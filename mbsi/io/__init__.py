"""
Data input/output module — universal spatial omics ingestion layer.

Supported platforms
-------------------
10x Visium / Visium HD  : mbsi.io.visium
10x Xenium              : mbsi.io.xenium
MERFISH / MERSCOPE      : mbsi.io.merfish
NanoString CosMx        : mbsi.io.cosmx
CODEX / PhenoCycler     : mbsi.io.codex
Generic h5ad / CSV / MEX: mbsi.io.generic

Auto-detection
--------------
    from mbsi.io import detect_platform, load_any
    result = detect_platform(file_names)   # DetectionResult
    adata  = load_any(zip_or_path)         # AnnData (MBSI contract)

Internal contract helpers
-------------------------
    from mbsi.io.converters import to_mbsi_contract, compute_readiness
    from mbsi.io.detect import compute_compatibility_matrix
"""

from mbsi.io.detect import detect_platform, compute_compatibility_matrix, DetectionResult
from mbsi.io.converters import to_mbsi_contract, compute_readiness
from mbsi.io.generic import load_h5ad, load_csv_matrix, load_mex_dir, load_zip
from mbsi.io.visium import load_visium_dir, load_visium_zip
from mbsi.io.xenium import load_xenium_dir, load_xenium_zip
from mbsi.io.merfish import load_merfish_dir, load_merfish_zip
from mbsi.io.cosmx import load_cosmx_dir, load_cosmx_zip
from mbsi.io.codex import load_codex_dir, load_codex_zip

# Legacy aliases so existing code keeps working
from mbsi.io.loaders import load_visium, load_counts_and_coords
from mbsi.io.validators import validate_spatial_adata


def load_any(source, platform: str = "auto") -> "anndata.AnnData":
    """
    Universal loader: auto-detect platform and load from any source.

    Parameters
    ----------
    source : str, Path, or file-like
        File path, directory path, or uploaded file object.
        ZIP archives are auto-extracted and platform-detected.
    platform : str
        Override auto-detection: 'visium', 'xenium', 'merfish',
        'cosmx', 'codex', 'h5ad', 'csv', or 'auto' (default).

    Returns
    -------
    adata : AnnData  (MBSI contract — see mbsi.io.converters)
    """
    from pathlib import Path

    if hasattr(source, "read"):
        # File-like object — peek at name to decide
        name = getattr(source, "name", "")
        if name.endswith(".h5ad"):
            return load_h5ad(source)
        if name.endswith(".zip"):
            return load_zip(source)
        if name.endswith(".csv"):
            return load_csv_matrix(source)
        return load_zip(source)  # assume ZIP if unknown

    path = Path(source)
    if path.is_dir():
        if platform == "auto":
            files = [f.name for f in path.rglob("*") if f.is_file()]
            result = detect_platform(files)
            platform = result.platform or "h5ad"

        loaders = {
            "visium": load_visium_dir,
            "xenium": load_xenium_dir,
            "merfish": load_merfish_dir,
            "cosmx": load_cosmx_dir,
            "codex": load_codex_dir,
        }
        if platform in loaders:
            return loaders[platform](path)
        raise ValueError(f"Cannot load directory as platform '{platform}'")

    if path.suffix == ".h5ad":
        return load_h5ad(path)
    if path.suffix == ".zip":
        return load_zip(path)
    if path.suffix in (".csv", ".tsv"):
        return load_csv_matrix(path, separator="\t" if path.suffix == ".tsv" else ",")

    raise ValueError(f"Unsupported file type: {path.suffix}")


__all__ = [
    # Auto-detect & universal
    "detect_platform",
    "compute_compatibility_matrix",
    "DetectionResult",
    "load_any",
    # Contract helpers
    "to_mbsi_contract",
    "compute_readiness",
    # Platform loaders
    "load_visium_dir",
    "load_visium_zip",
    "load_xenium_dir",
    "load_xenium_zip",
    "load_merfish_dir",
    "load_merfish_zip",
    "load_cosmx_dir",
    "load_cosmx_zip",
    "load_codex_dir",
    "load_codex_zip",
    # Generic
    "load_h5ad",
    "load_csv_matrix",
    "load_mex_dir",
    "load_zip",
    # Legacy
    "load_visium",
    "load_counts_and_coords",
    "validate_spatial_adata",
]
