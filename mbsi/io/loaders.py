"""
Data loaders for spatial transcriptomics data.

Legacy module — delegates to mbsi.io generic/visium implementations.
"""

from pathlib import Path
from typing import Union

import anndata as ad
import numpy as np

from mbsi.io.generic import load_h5ad, load_csv_matrix_coords
from mbsi.io.visium import load_space_ranger


def load_visium(path: Union[str, Path]) -> ad.AnnData:
    """Load 10x Visium Space Ranger outs directory or ZIP."""
    adata, _ = load_space_ranger(path)
    return adata


def load_counts_and_coords(
    counts_path: Union[str, Path],
    coords_path: Union[str, Path],
    counts_format: str = "csv",
) -> ad.AnnData:
    """Load count matrix and spatial coordinates from files."""
    import pandas as pd

    if counts_format == "csv":
        counts = pd.read_csv(counts_path, index_col=0)
    elif counts_format == "tsv":
        counts = pd.read_csv(counts_path, sep="\t", index_col=0)
    else:
        raise ValueError(f"Unsupported format: {counts_format}")
    coords = pd.read_csv(coords_path)
    return load_csv_matrix_coords(counts, coords)


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    from PIL import Image
    return np.array(Image.open(image_path))


def load_segmentation(mask_path: Union[str, Path]) -> np.ndarray:
    from PIL import Image
    return np.array(Image.open(mask_path))
