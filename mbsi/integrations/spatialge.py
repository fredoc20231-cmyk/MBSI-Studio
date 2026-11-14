"""Optional spatialGE 2.x execution bridge for observed spatial transcriptomics.

No R package is vendored: the upstream spatialGE package runs through Rscript.
The bridge exports per-sample observed raw counts and coordinates; R performs
spatialGE analysis with its own published implementations. Never interpret
pooled spatial coordinates as one tissue.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from scipy import sparse

SUPPORTED_OPERATIONS = frozenset({
    "transform_data", "filter_data", "STclust", "SThet",
    "compare_SThet", "STenrich", "STgradient", "STdiff", "STniche",
    "plot_stniche", "STplot", "gene_interpolation", "STplot_interpolation",
    "pseudobulk_samples", "pseudobulk_dim_plot", "pseudobulk_heatmap",
    "distribution_plots", "plot_counts", "get_gene_meta",
    "summarize_STlist",
})
# Explicit limit: spatialGE's generic TSV import densifies. Use small to
# moderate datasets; do not silently densify large Xenium/CosMx datasets.
DEFAULT_MAX_EXPORT_ELEMENTS = 10_000_000


def _validate_counts(sample, sample_id: str):
    if sample.n_obs < 2 or sample.n_vars < 1:
        raise ValueError(f"{sample_id}: need >=2 spots/cells and >=1 gene")
    if not sample.var_names.is_unique or not sample.obs_names.is_unique:
        raise ValueError(f"{sample_id}: gene and observation identifiers must be unique")
    matrix = sample.layers["counts"] if "counts" in sample.layers else sample.X
    values = matrix.data if sparse.issparse(matrix) else np.asarray(matrix)
    if not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values, np.rint(values)):
        raise ValueError(f"{sample_id}: require observed nonnegative integer raw counts")
    coords = sample.obsm.get("spatial")
    if coords is None:
        raise ValueError(f"{sample_id}: missing obsm['spatial']")
    coords = np.asarray(coords)
    if coords.shape != (sample.n_obs, 2) or not np.isfinite(coords).all():
        raise ValueError(f"{sample_id}: spatial coordinates must be finite Nx2")
    return matrix, coords


def prepare_spatialge_inputs(
    samples: Mapping[str, object],
    output_dir: str | Path,
    *,
    max_export_elements: int = DEFAULT_MAX_EXPORT_ELEMENTS,
) -> Path:
    """Export valid raw AnnData samples to spatialGE's documented TSV interface.

    Each genes-by-observations TSV and coordinate TSV retains the exact
    feature/spot identifiers. The manifest records original sample identities.
    This export never fabricates cells, masks, gene expression, or coordinates.
    """
    if not samples:
        raise ValueError("Provide at least one observed sample")
    if max_export_elements < 1:
        raise ValueError("max_export_elements must be positive")
    out = Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Output directory must be empty: " + str(out))
    # Complete validation before writing any payloads.
    validated = []
    for idx, (sample_id, sample) in enumerate(samples.items(), 1):
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError("Sample names must be nonempty strings")
        matrix, coords = _validate_counts(sample, sample_id)
        if sample.n_vars * sample.n_obs > max_export_elements:
            raise ValueError(
                f"{sample_id}: generic TSV export would require "
                f"{sample.n_vars * sample.n_obs:,} elements; maximum is "
                f"{max_export_elements:,}. Use a native spatialGE sample directory "
                "or increase the explicit limit only with adequate memory."
            )
        validated.append((f"MB{idx:06d}", sample_id, sample, matrix, coords))
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"format": "mbsi-spatialge-tsv-v1", "samples": [],
                "source": "observed_raw_counts", "coordinate_unit": "as_supplied"}
    sample_metadata = []
    for alias, sample_id, sample, matrix, coords in validated:
        counts_file = alias + "_counts.tsv"
        coords_file = alias + "_coords.tsv"
        # spatialGE requires genes in rows and spots/cells in columns.
        matrix_by_gene = (
            matrix.tocsc().T.tocsr() if sparse.issparse(matrix)
            else np.asarray(matrix).T
        )
        with (out / counts_file).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["gene", *map(str, sample.obs_names)])
            for i, gene in enumerate(sample.var_names):
                row = (matrix_by_gene.getrow(i).toarray().ravel()
                       if sparse.issparse(matrix_by_gene) else matrix_by_gene[i])
                writer.writerow([str(gene), *[int(v) for v in row]])
        with (out / coords_file).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            writer.writerow(["libname", "ypos", "xpos"])
            for observation, (x, y) in zip(sample.obs_names, coords):
                writer.writerow([str(observation), float(y), float(x)])
        sample_metadata.append({"sample_id": alias, "original_sample_id": sample_id})
        manifest["samples"].append({
            "alias": alias, "original_id": sample_id,
            "counts": counts_file, "coordinates": coords_file,
            "n_observations": sample.n_obs, "n_genes": sample.n_vars
        })
    with (out / "samples.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "original_sample_id"])
        writer.writeheader()
        writer.writerows(sample_metadata)
    path = out / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def run_spatialge(
    manifest_path: str | Path,
    operations: Sequence[Mapping[str, object]],
    *,
    rscript: str = "Rscript",
    timeout_seconds: int = 3600,
) -> dict:
    """Run an allowlisted spatialGE workflow in a separate R process.

    Operations are e.g. [{"method":"transform_data","params":{"method":"log"}},
    {"method":"SThet","params":{"genes":["TP53"],"method":["moran","geary"]}}].
    All other methods are opt-in; no synthetic fallback and no shell invocation.
    """
    manifest_path = Path(manifest_path).resolve(strict=True)
    if not manifest_path.is_file() or manifest_path.name != "manifest.json":
        raise ValueError("Expected manifest.json from prepare_spatialge_inputs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "mbsi-spatialge-tsv-v1":
        raise ValueError("Unsupported bridge manifest format")
    if not operations:
        raise ValueError("Select at least one spatialGE operation")
    safe_ops = []
    for spec in operations:
        if not isinstance(spec, Mapping):
            raise TypeError("Each operation must be a mapping")
        method = spec.get("method")
        params = spec.get("params", {})
        if method not in SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported spatialGE operation: {method}")
        if not isinstance(params, dict) or any(
            not isinstance(k, str) or k in {"x", "out_i", "zi"}
            for k in params
        ):
            raise ValueError("Invalid or protected spatialGE parameters")
        safe_ops.append({"method": method, "params": params})
    # Validate JSON encodability before starting R.
    payload = json.dumps({"operations": safe_ops}, allow_nan=False)
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")
    executable = shutil.which(rscript)
    if executable is None:
        raise RuntimeError("Rscript not found; install R and spatialGE >=2.0.0")
    runner = Path(__file__).with_name("spatialge_runner.R")
    if not runner.is_file():
        raise FileNotFoundError(runner)
    root = manifest_path.parent
    config_path = root / "operations.json"
    config_path.write_text(payload, encoding="utf-8")
    result = subprocess.run(
        [executable, str(runner), str(manifest_path), str(config_path)],
        cwd=str(root), capture_output=True, text=True, timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"spatialGE R backend failed (exit {result.returncode}): "
            + result.stderr[-4000:]
        )
    result_path = root / "results" / "summary.json"
    if not result_path.is_file():
        raise RuntimeError("spatialGE exited without generating results/summary.json")
    return json.loads(result_path.read_text(encoding="utf-8"))
