"""Universal spatial omics ingestion — Phase 1."""

from mbsi.io.detect import detect_platform
from mbsi.io.validators import (
    validate_adata_contract,
    validate_spatial_adata,
    validate_spatial_coords,
    compute_readiness,
)
from mbsi.io.converters import normalize_to_contract
from mbsi.io.visium import load_space_ranger
from mbsi.io.generic import load_h5ad, load_csv_matrix_coords, ingest_h5ad, ingest_csv_matrix_coords
from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.ingest import ingest_upload, save_upload_to_temp

# Backward-compatible loaders module re-exports
from mbsi.io.loaders import load_visium, load_counts_and_coords

__all__ = [
    "detect_platform",
    "validate_adata_contract",
    "validate_spatial_adata",
    "validate_spatial_coords",
    "compute_readiness",
    "normalize_to_contract",
    "load_space_ranger",
    "load_h5ad",
    "load_csv_matrix_coords",
    "load_visium",
    "load_counts_and_coords",
    "ingest_h5ad",
    "ingest_csv_matrix_coords",
    "ingest_upload",
    "save_upload_to_temp",
    "get_compatibility_matrix",
]
