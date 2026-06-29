"""Reference mapping via atlas registry."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad

from mbsi.multimodal.seurat_like.reference_mapping import run_reference_mapping
from mbsi.references.atlas_registry import get_atlas_metadata, load_atlas


def map_to_reference_atlas(
    query: ad.AnnData,
    atlas_id: str,
) -> Dict[str, Any]:
    """Map query to a registered reference atlas."""
    meta = get_atlas_metadata(atlas_id)
    if meta is None:
        return {"error": f"Unknown atlas: {atlas_id}"}
    reference = load_atlas(atlas_id)
    if reference is None:
        return {
            "error": f"Atlas {atlas_id} not loaded — upload reference h5ad or register loader",
            "atlas_metadata": meta,
        }
    label_key = meta.get("label_key", "cell_type")
    return run_reference_mapping(query, reference, atlas_id=atlas_id, ref_label_key=label_key)
