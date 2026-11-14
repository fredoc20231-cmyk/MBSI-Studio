"""No R installation needed for boundary and export contract tests."""
from __future__ import annotations

import csv
import json
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from mbsi.integrations.spatialge import (
    prepare_spatialge_inputs, run_spatialge, SUPPORTED_OPERATIONS
)


class ObservedSample:
    def __init__(self, counts, genes=("TP53", "CD3D"), *,
                 sparse_input=False, coords=True):
        x = np.asarray(counts, dtype=float)
        self.X = sparse.csr_matrix(x) if sparse_input else x
        self.layers = {"counts": self.X}
        self.n_obs, self.n_vars = x.shape
        self.var_names = pd.Index(genes)
        self.obs_names = pd.Index(f"spot_{i}" for i in range(self.n_obs))
        self.obs = pd.DataFrame({"cluster": ["C1"] * self.n_obs}, index=self.obs_names)
        self.obsm = {}
        if coords:
            self.obsm["spatial"] = np.column_stack(
                (np.arange(self.n_obs, dtype=float),
                 np.arange(self.n_obs, dtype=float) + 7)
            )


def test_export_two_real_samples_and_orientation(tmp_path):
    samples = {
        "tumor": ObservedSample([[1, 0], [3, 2]], sparse_input=True),
        "control": ObservedSample([[2, 1], [0, 4]])
    }
    path = prepare_spatialge_inputs(samples, tmp_path / "bridge",
        sample_metadata={"tumor": {"condition": "Case", "batch_id": "B1"},
                         "control": {"condition": "Control", "batch_id": "B2"}})
    manifest = json.loads(path.read_text())
    assert [row["original_id"] for row in manifest["samples"]] == ["tumor", "control"]
    meta = pd.read_csv(path.parent / "samples.csv")
    assert meta["condition"].tolist() == ["Case", "Control"]
    assert meta["batch_id"].tolist() == ["B1", "B2"]
    assert "patient_id" not in meta.columns
    with (path.parent / "MB000001_counts.tsv").open() as f:
        rows = list(csv.reader(f, delimiter="\t"))
    assert rows == [["gene", "spot_0", "spot_1"], ["TP53", "1", "3"], ["CD3D", "0", "2"]]
    with (path.parent / "MB000001_coords.tsv").open() as f:
        coords = list(csv.reader(f, delimiter="\t"))
    assert coords[0] == ["libname", "ypos", "xpos"]
    assert coords[1] == ["spot_0", "7.0", "0.0"]
    assert manifest["samples"][0]["annotations"] == "MB000001_annotations.tsv"
    with (path.parent / "MB000001_annotations.tsv").open() as f:
        labels = list(csv.reader(f, delimiter="\t"))
    assert labels == [["libname", "cluster"], ["spot_0", "C1"], ["spot_1", "C1"]]


def test_rejects_noncounts_missing_coords_and_overlarge_export(tmp_path):
    with pytest.raises(ValueError, match="integer raw counts"):
        prepare_spatialge_inputs({"s": ObservedSample([[1.2, 0], [0, 1]])}, tmp_path / "a")
    with pytest.raises(ValueError, match="spatial"):
        prepare_spatialge_inputs({"s": ObservedSample([[1, 0], [0, 1]], coords=False)}, tmp_path / "b")
    with pytest.raises(ValueError, match="maximum"):
        prepare_spatialge_inputs({"s": ObservedSample([[1, 0], [0, 1]])},
                                 tmp_path / "c", max_export_elements=2)


def test_export_fails_closed_on_existing_output(tmp_path):
    output = tmp_path / "bridge"
    output.mkdir()
    (output / "sentinel.txt").write_text("unchanged")
    with pytest.raises(FileExistsError):
        prepare_spatialge_inputs(
            {"s": ObservedSample([[1, 0], [0, 1]])}, output)
    assert (output / "sentinel.txt").read_text() == "unchanged"


def test_run_rejects_unrecognized_or_protected_methods_before_rscript(tmp_path):
    manifest = prepare_spatialge_inputs(
        {"s": ObservedSample([[1, 0], [0, 1]])}, tmp_path / "bridge")
    assert "STniche" in SUPPORTED_OPERATIONS
    with pytest.raises(ValueError, match="Unsupported"):
        run_spatialge(manifest, [{"method": "system", "params": {}}])
    with pytest.raises(ValueError, match="protected"):
        run_spatialge(manifest, [{"method": "SThet", "params": {"x": "override"}}])


def test_missing_rscript_reports_installation_requirement(tmp_path):
    manifest = prepare_spatialge_inputs(
        {"s": ObservedSample([[1, 0], [0, 1]])}, tmp_path / "bridge")
    with pytest.raises(RuntimeError, match="Rscript not found"):
        run_spatialge(manifest,
                      [{"method": "transform_data", "params": {"method": "log"}}],
                      rscript="definitely-not-present-123456")
