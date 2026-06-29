"""Backed AnnData for large datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import anndata as ad


def use_backed_h5ad(path: Union[str, Path], mode: str = "r") -> ad.AnnData:
    """Open h5ad in backed mode for memory-efficient access."""
    return ad.read_h5ad(str(path), backed=mode)
