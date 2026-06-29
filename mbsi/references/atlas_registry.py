"""Reference atlas registry."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import anndata as ad

AtlasLoader = Callable[[], ad.AnnData]

ATLAS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "human_pancreas": {
        "label": "Human pancreas (scRNA reference)",
        "species": "human",
        "tissue": "pancreas",
        "label_key": "cell_type",
        "n_cells": 4000,
        "source": "builtin_stub",
    },
    "mouse_brain": {
        "label": "Mouse brain (spatial reference)",
        "species": "mouse",
        "tissue": "brain",
        "label_key": "cluster",
        "n_cells": 5000,
        "source": "builtin_stub",
    },
    "human_tumor_microenvironment": {
        "label": "Human TME atlas",
        "species": "human",
        "tissue": "tumor",
        "label_key": "cell_type",
        "n_cells": 8000,
        "source": "builtin_stub",
    },
}

_LOADERS: Dict[str, AtlasLoader] = {}


def register_atlas(atlas_id: str, loader: AtlasLoader) -> None:
    _LOADERS[atlas_id] = loader


def list_atlases() -> List[str]:
    return list(ATLAS_REGISTRY.keys())


def get_atlas_metadata(atlas_id: str) -> Optional[Dict[str, Any]]:
    meta = ATLAS_REGISTRY.get(atlas_id)
    return dict(meta) if meta else None


def load_atlas(atlas_id: str) -> Optional[ad.AnnData]:
    if atlas_id in _LOADERS:
        return _LOADERS[atlas_id]()
    return None
