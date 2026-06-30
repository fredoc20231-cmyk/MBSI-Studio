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
from mbsi.io.stereo_seq import (
    detect_stereo_seq,
    load_stereo_seq_dataset,
    compute_stereo_seq_readiness,
)
from mbsi.io.generic import load_h5ad, load_csv_matrix_coords, ingest_h5ad, ingest_csv_matrix_coords
from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.ingest import ingest_upload, save_upload_to_temp
from mbsi.io.ingest_universal import IngestionResult, ingest_dataset
from mbsi.io.stereo_seq import detect_stereo_seq_assets, load_stereo_qc_html

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
    "detect_stereo_seq",
    "load_stereo_seq_dataset",
    "compute_stereo_seq_readiness",
    "load_h5ad",
    "load_csv_matrix_coords",
    "load_visium",
    "load_counts_and_coords",
    "ingest_h5ad",
    "ingest_csv_matrix_coords",
    "ingest_upload",
    "save_upload_to_temp",
    "ingest_dataset",
    "IngestionResult",
    "get_compatibility_matrix",
    "detect_stereo_seq_assets",
    "load_stereo_qc_html",
]
