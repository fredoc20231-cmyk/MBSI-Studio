"""Map transcript coordinates to segmented cell labels and build AnnData."""

from __future__ import annotations

from typing import Optional, Union

import anndata as ad
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix


def map_transcripts_to_labels(
    transcript_df: pd.DataFrame,
    label_mask: np.ndarray,
    x_col: str = "x",
    y_col: str = "y",
    gene_col: str = "gene",
) -> pd.DataFrame:
    """Assign each transcript to a cell label based on pixel coordinates."""
    label_mask = np.asarray(label_mask, dtype=np.int32)
    h, w = label_mask.shape[:2]

    xs = pd.to_numeric(transcript_df[x_col], errors="coerce").fillna(-1).astype(int).values
    ys = pd.to_numeric(transcript_df[y_col], errors="coerce").fillna(-1).astype(int).values

    labels = np.zeros(len(transcript_df), dtype=np.int32)
    valid = (xs >= 0) & (ys >= 0) & (xs < w) & (ys < h)
    labels[valid] = label_mask[ys[valid], xs[valid]]

    out = transcript_df.copy()
    out["cell_label"] = labels
    out["assigned"] = labels > 0
    return out


def build_cell_by_gene_anndata(
    transcript_df: pd.DataFrame,
    label_mask: np.ndarray,
    pixel_to_micron_ratio: float = 1.0,
    x_col: str = "x",
    y_col: str = "y",
    gene_col: str = "gene",
) -> ad.AnnData:
    """Build cell-by-gene AnnData from transcript assignments."""
    mapped = map_transcripts_to_labels(
        transcript_df,
        label_mask,
        x_col=x_col,
        y_col=y_col,
        gene_col=gene_col,
    )
    assigned = mapped[mapped["cell_label"] > 0].copy()
    if assigned.empty:
        raise ValueError("No transcripts assigned to cells")

    counts = (
        assigned.groupby(["cell_label", gene_col], observed=True)
        .size()
        .unstack(fill_value=0)
        .astype(np.int32)
    )
    genes = counts.columns.astype(str).tolist()
    cell_labels = counts.index.astype(int).tolist()

    X = csr_matrix(counts.values)
    adata = ad.AnnData(X=X)
    adata.obs_names = [f"cell_{label}" for label in cell_labels]
    adata.var_names = genes

    centroids = []
    h, w = label_mask.shape[:2]
    for label in cell_labels:
        ys, xs = np.where(label_mask == label)
        if len(xs):
            cx = float(np.mean(xs)) * pixel_to_micron_ratio
            cy = float(np.mean(ys)) * pixel_to_micron_ratio
        else:
            cx, cy = 0.0, 0.0
        centroids.append([cx, cy])
    adata.obsm["spatial"] = np.asarray(centroids, dtype=np.float32)
    adata.obs["cell_label"] = cell_labels
    adata.uns["mbsi_transcript_mapping"] = {
        "n_transcripts": int(len(transcript_df)),
        "n_assigned": int(assigned.shape[0]),
        "percent_assigned": round(100.0 * assigned.shape[0] / max(len(transcript_df), 1), 2),
    }
    return adata
