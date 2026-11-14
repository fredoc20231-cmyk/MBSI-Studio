"""Read-only, backend-independent spatial browser data contract.

An AnnData adapter is provided today. Future API/R backends can implement the
same BrowserDataset protocol without changing the Streamlit presentation.
Coordinates remain sample-local and all expression values are observed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from scipy import sparse


@dataclass(frozen=True)
class SpatialView:
    sample_id: str
    barcodes: tuple[str, ...]
    x: np.ndarray
    y: np.ndarray
    values: np.ndarray
    label: str
    categorical: bool


@runtime_checkable
class BrowserDataset(Protocol):
    def samples(self) -> list[str]: ...
    def genes(self) -> list[str]: ...
    def features(self) -> list[str]: ...
    def view(self, sample_id: str, feature: str) -> SpatialView: ...
    def summary(self, feature: str) -> list[dict]: ...


class AnnDataBrowserAdapter:
    """Adapt one or many observed AnnData objects to the browser contract."""

    def __init__(self, samples: dict[str, object]):
        if not samples:
            raise ValueError("Upload observed spatial data first")
        self._samples = {}
        for sid, adata in samples.items():
            if not isinstance(sid, str) or not sid:
                raise ValueError("Sample ID must be nonempty")
            coords = adata.obsm.get("spatial")
            if coords is None or np.shape(coords) != (adata.n_obs, 2):
                raise ValueError(f"{sid}: spatial coordinates must be Nx2")
            if not np.isfinite(coords).all():
                raise ValueError(f"{sid}: spatial coordinates must be finite")
            if not adata.var_names.is_unique or not adata.obs_names.is_unique:
                raise ValueError(f"{sid}: duplicate genes or barcodes")
            self._samples[sid] = adata

    def samples(self) -> list[str]:
        return list(self._samples)

    def genes(self) -> list[str]:
        """Shared genes only: every selected sample can display the same gene."""
        return sorted(set.intersection(*(set(a.var_names) for a in self._samples.values())))

    def features(self) -> list[str]:
        names = ("cluster", "leiden", "domain", "cell_type", "niche", "condition")
        return [n for n in names if all(n in a.obs for a in self._samples.values())]

    def view(self, sample_id: str, feature: str) -> SpatialView:
        if sample_id not in self._samples:
            raise KeyError(sample_id)
        a = self._samples[sample_id]
        categorical = feature in a.obs
        if categorical:
            values = a.obs[feature].astype(str).to_numpy()
        elif feature in a.var_names:
            x = a[:, [feature]].X
            values = np.asarray(x.toarray() if sparse.issparse(x) else x).ravel()
        else:
            raise KeyError(f"Feature not found: {feature}")
        coords = np.asarray(a.obsm["spatial"], dtype=float)
        return SpatialView(sample_id, tuple(map(str, a.obs_names)),
                           coords[:, 0], coords[:, 1], values, feature, categorical)

    def summary(self, feature: str) -> list[dict]:
        result = []
        for sid, a in self._samples.items():
            record = {"sample_id": sid, "observations": int(a.n_obs),
                      "genes": int(a.n_vars)}
            if feature in a.var_names:
                view = self.view(sid, feature)
                vals = np.asarray(view.values, dtype=float)
                record.update(mean_expression=float(vals.mean()),
                              detection_fraction=float((vals > 0).mean()))
            result.append(record)
        return result


def resolve_browser_samples(session: dict) -> dict[str, object]:
    """Resolve already-ingested data only; never create synthetic stand-ins."""
    samples = session.get("sample_adatas") or {}
    if samples:
        return dict(samples)
    paths = session.get("sample_adata_paths") or {}
    if paths:
        import anndata as ad
        return {str(sid): ad.read_h5ad(path) for sid, path in paths.items() if path}
    single = session.get("adata")
    if single is None:
        return {}
    if "sample_id" in single.obs and single.obs["sample_id"].nunique() > 1:
        return {str(sid): single[single.obs["sample_id"].astype(str) == str(sid)].copy()
                for sid in single.obs["sample_id"].astype(str).unique()}
    return {"sample_1": single}
