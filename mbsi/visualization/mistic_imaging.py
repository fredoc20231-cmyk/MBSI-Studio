"""Mistic-inspired multiplex image cohort embeddings, without synthetic features.

Source concept: MathOnco/Mistic (MIT, 2021 IMO). This implementation does not
copy upstream Bokeh code, and keeps t-SNE exploratory, not inferential.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class ImagingEmbedding:
    image_ids: tuple[str, ...]
    x: np.ndarray
    y: np.ndarray
    source: str
    metadata: list[dict[str, Any]]

    def records(self) -> list[dict[str, Any]]:
        return [{"image_id": key, "x": float(self.x[i]), "y": float(self.y[i]),
                 **self.metadata[i]} for i, key in enumerate(self.image_ids)]


def _validate(ids: Sequence[str], features: np.ndarray) -> np.ndarray:
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != len(ids) or values.shape[1] == 0:
        raise ValueError("Image feature matrix must have one row per image")
    if len(ids) < 3 or len(set(ids)) != len(ids) or not all(isinstance(k, str) and k for k in ids):
        raise ValueError("Need at least 3 unique nonempty image identifiers")
    if not np.isfinite(values).all():
        raise ValueError("Image features must all be finite")
    return values


def image_cohort_embedding(
    image_ids: Sequence[str],
    features: np.ndarray,
    *,
    metadata: Mapping[str, Mapping[str, Any]] | None = None,
    method: str = "pca",
    random_state: int = 42,
    perplexity: float = 30.0,
) -> ImagingEmbedding:
    """Project observed per-image marker/morphology features to a 2D cohort view.

    Accepts externally extracted *observed* feature matrices. For a supplied
    t-SNE layout, use image_cohort_layout instead. Does not invent images,
    coordinates, labels, patient outcomes or histologic inference.
    """
    values = _validate(image_ids, features)
    scaled = StandardScaler().fit_transform(values)
    if method == "pca" and min(scaled.shape) < 2:
        raise ValueError("PCA visualization requires at least two measured image features")
    if method == "pca":
        coords = PCA(n_components=2, random_state=random_state).fit_transform(scaled)
    elif method == "tsne":
        if not 0 < perplexity < len(image_ids):
            raise ValueError("t-SNE perplexity must be below the number of images")
        coords = TSNE(
            n_components=2, perplexity=perplexity, random_state=random_state,
            init="pca" if scaled.shape[1] >= 2 else "random",
            learning_rate="auto",
        ).fit_transform(scaled)
    else:
        raise ValueError("method must be 'pca' or 'tsne'")
    return image_cohort_layout(image_ids, coords, metadata=metadata,
                               source=f"computed_{method}_from_observed_features")


def image_cohort_layout(
    image_ids: Sequence[str],
    coordinates: np.ndarray,
    *,
    metadata: Mapping[str, Mapping[str, Any]] | None = None,
    source: str = "user_supplied_embedding",
) -> ImagingEmbedding:
    """Validate a supplied 2D image embedding and metadata alignment."""
    coords = np.asarray(coordinates, dtype=float)
    if coords.shape != (len(image_ids), 2) or not np.isfinite(coords).all():
        raise ValueError("Finite Nx2 embedding required")
    if len(set(image_ids)) != len(image_ids) or not all(isinstance(k, str) and k for k in image_ids):
        raise ValueError("Image IDs must be unique nonempty strings")
    meta = metadata or {}
    records = [dict(meta.get(key, {})) for key in image_ids]
    if any("image_id" in record or "x" in record or "y" in record for record in records):
        raise ValueError("Metadata may not replace image IDs or embedding coordinates")
    return ImagingEmbedding(tuple(image_ids), coords[:, 0], coords[:, 1], source, records)
