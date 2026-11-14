import { describe, expect, it } from "vitest";
import {
  alignScalarMetrics,
  buildComparisonRequests,
  COMPARISON_LEVELS,
  getObservedDetails,
} from "@/lib/comparison";

describe("multi-sample comparison", () => {
  it("creates one observed-data workflow request for every selected sample", () => {
    const expression = COMPARISON_LEVELS.find((level) => level.id === "expression")!;
    const requests = buildComparisonRequests(expression, ["dataset-a", "dataset-b", "dataset-c"]);

    expect(requests).toHaveLength(3);
    expect(requests.map((request) => request.dataset_id)).toEqual([
      "dataset-a",
      "dataset-b",
      "dataset-c",
    ]);
    expect(requests.every((request) => request.module === "spatial_analysis")).toBe(true);
    expect(requests.every((request) => request.allow_demo === false)).toBe(true);
  });

  it("does not run a comparison with fewer than two samples", () => {
    const clusters = COMPARISON_LEVELS.find((level) => level.id === "clusters")!;

    expect(buildComparisonRequests(clusters, ["dataset-a"])).toEqual([]);
  });

  it("never submits unavailable scientific workflows", () => {
    for (const id of ["niches", "interactions", "trajectories"]) {
      const level = COMPARISON_LEVELS.find((item) => item.id === id)!;
      expect(buildComparisonRequests(level, ["dataset-a", "dataset-b"])).toEqual([]);
    }
  });

  it("aligns observed scalar values without inventing missing results", () => {
    const rows = alignScalarMetrics([
      { datasetId: "dataset-a", outputs: { n_clusters: 4 } },
      { datasetId: "dataset-b", outputs: { n_genes: 10 } },
    ]);

    expect(rows).toEqual([
      { key: "n_clusters", values: { "dataset-a": 4, "dataset-b": null } },
      { key: "n_genes", values: { "dataset-a": null, "dataset-b": 10 } },
    ]);
  });

  it("extracts only returned level-specific details", () => {
    const details = getObservedDetails(
      { seurat_like_results: { de_results: [{ gene: "observed-gene" }] } },
      [
        ["seurat_like_results", "de_results"],
        ["seurat_like_results", "missing"],
      ],
    );

    expect(details).toEqual({
      "seurat_like_results.de_results": [{ gene: "observed-gene" }],
    });
  });
});
