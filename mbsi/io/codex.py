"""CODEX loader — Phase 3 stub."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import anndata as ad


def load_codex(path) -> Tuple[ad.AnnData, Dict[str, Any]]:
    raise NotImplementedError(
        "CODEX ingestion is partial support stub — export cell intensity matrix + coordinates as CSV/h5ad"
    )
