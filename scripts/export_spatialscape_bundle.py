"""Offline, opt-in export of registered MBSI datasets to spatialscape v1 bundles.

Requires a separate spatialscape==1.0.0 installation for --build.
Never expose generated bundles publicly without access controls and data review.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import anndata as ad
import numpy as np
import yaml

VALID_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
SAFE_FIELDS = ("cluster", "leiden", "domain", "cell_type", "niche", "condition")
PLATFORMS = {"visium", "visium_hd", "xenium", "merfish", "codex"}
PROVENANCE = {
    "source": "MBSI Studio server-owned ingested AnnData",
    "viewer": "spatialscape",
    "viewer_version": "1.0.0",
    "viewer_license": "MIT; copyright (c) 2026 Michael Totty",
    "citation": "Totty M. spatialscape (2026), https://doi.org/10.5281/zenodo.24376035",
    "warning": "Source data and built bundles can contain sensitive expression and metadata. "
               "Do not publish without data governance review.",
}


def _safe_source(registry_root: Path, dataset_id: str):
    if not VALID_ID.fullmatch(dataset_id):
        raise ValueError("Invalid dataset id")
    registry = registry_root.resolve()
    record_path = registry / "datasets" / (dataset_id + ".json")
    if not record_path.is_file():
        raise FileNotFoundError("Dataset not found in local MBSI registry")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    source = Path(record.get("adata_path") or "").resolve()
    allowed = (registry / "ingested").resolve()
    if not source.is_relative_to(allowed) or not source.is_file() or source.suffix != ".h5ad":
        raise ValueError("Dataset must refer to a server-ingested h5ad")
    return record, source


def prepare_config(
    registry_root: Path,
    dataset_ids: list[str],
    bundle_id: str,
    name: str,
    *,
    already_microns: bool = False,
    microns_per_unit: float | None = None,
):
    if not VALID_ID.fullmatch(bundle_id):
        raise ValueError("Invalid output bundle id")
    if not dataset_ids or len(set(dataset_ids)) != len(dataset_ids):
        raise ValueError("Provide at least one distinct dataset id")
    if already_microns == (microns_per_unit is not None):
        raise ValueError("Specify exactly one of --already-microns or --microns-per-unit")
    if microns_per_unit is not None and (not np.isfinite(microns_per_unit) or microns_per_unit <= 0):
        raise ValueError("Microns per unit must be finite and positive")
    microns = {"already_microns": True} if already_microns else {
        "microns_per_unit": float(microns_per_unit)
    }
    samples = []
    for dataset_id in dataset_ids:
        record, source = _safe_source(registry_root, dataset_id)
        a = ad.read_h5ad(source, backed="r")
        try:
            if "spatial" not in a.obsm:
                raise ValueError("Missing spatial coordinates for " + dataset_id)
            coords = np.asarray(a.obsm["spatial"])
            if coords.shape != (a.n_obs, 2) or not np.isfinite(coords).all():
                raise ValueError("Invalid source coordinates for " + dataset_id)
            fields = {key: key for key in SAFE_FIELDS if key in a.obs.columns}
        finally:
            a.file.close()
        platform = str(record.get("platform", "other")).lower()
        samples.append({
            "id": dataset_id,
            "name": str(record.get("sample_id") or dataset_id),
            "platform": platform if platform in PLATFORMS else "other",
            "path": str(source),
            "coords": "obsm/spatial",
            "microns": microns.copy(),
            "fields": fields,
            "images": [],
            "segmentations": [],
        })
    return {
        "id": bundle_id,
        "name": name,
        "description": "Observed MBSI ingested data; no cell inference or statistical testing.",
        "layout": {"mode": "grid"},
        "samples": samples,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_ids", nargs="+", help="IDs from the MBSI ingested dataset registry")
    parser.add_argument("--registry", type=Path, default=Path("data/registry"))
    parser.add_argument("--out", type=Path, required=True, help="Private local output directory")
    parser.add_argument("--id", default="mbsi_atlas", dest="bundle_id")
    parser.add_argument("--name", default="MBSI observed spatial atlas")
    scale = parser.add_mutually_exclusive_group(required=True)
    scale.add_argument("--already-microns", action="store_true")
    scale.add_argument("--microns-per-unit", type=float)
    parser.add_argument("--build", action="store_true",
                        help="Run installed spatialscape CLI build and validate after generating YAML")
    args = parser.parse_args(argv)
    cfg = prepare_config(
        args.registry, args.dataset_ids, args.bundle_id, args.name,
        already_microns=args.already_microns, microns_per_unit=args.microns_per_unit,
    )
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg_path = out / "dataset.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    (out / "MBSI_PROVENANCE.json").write_text(json.dumps(PROVENANCE, indent=2), encoding="utf-8")
    print("Wrote", cfg_path)
    if args.build:
        exe = shutil.which("spatialscape")
        if not exe:
            raise SystemExit("Install spatialscape==1.0.0 in this local environment before --build")
        bundle = out / "bundles" / args.bundle_id
        subprocess.run([exe, "build", str(cfg_path), "--out", str(bundle)], check=True, timeout=7200)
        subprocess.run([exe, "validate", str(bundle)], check=True, timeout=1200)
        print("Validated private bundle:", bundle)


if __name__ == "__main__":
    main()
