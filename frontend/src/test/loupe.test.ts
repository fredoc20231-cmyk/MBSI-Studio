import { afterEach, describe, expect, it, vi } from "vitest";
import {
  LOUPE_FUNCTIONS,
  LoupeCapabilitiesSchema,
  loupeArtifactPath,
  loupeBlockedReason,
  safeOutputName,
  type LoupeCapabilities,
} from "@/lib/loupe";
import { mbsi } from "@/lib/mbsi-api";
import { saveApiConnection } from "@/lib/mbsi-connection";

const caps: LoupeCapabilities = {
  contract_version: 1,
  runtime: { r: "4.4.0", loupeR: "1.1.5", hdf5: "1.14.0", louper: "1.1.5", license_ready: true },
  operations: [{ function: "create_loupe", available: true }],
  image_formats: [],
};
const run = {
  id: "run-1",
  dataset_id: "observed-1",
  function: "create_loupe",
  status: "completed",
  outputs: {},
  artifacts: [],
  warnings: [],
};
afterEach(() => {
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

describe("Loupe external scientific boundary", () => {
  it("reflects every exported function in the uploaded loupeR NAMESPACE", () => {
    expect(LOUPE_FUNCTIONS.map((f) => f.name).sort()).toEqual(
      [
        "counts_matrix_from_assay",
        "create_bugreport",
        "create_bugreport_from_seurat",
        "create_hdf5",
        "create_loupe",
        "create_loupe_from_seurat",
        "read_feature_ids_from_tsv",
        "select_assay",
        "select_clusters",
        "select_projections",
        "setup",
        "validate_barcodes",
        "validate_clusters",
        "validate_count_mat",
        "validate_projections",
      ].sort(),
    );
  });
  it("never enables functions before the service reports availability", () => {
    expect(loupeBlockedReason(undefined, "create_loupe", "observed-1")).not.toBe("");
    expect(loupeBlockedReason(caps, "select_assay", "observed-1")).not.toBe("");
    expect(loupeBlockedReason(caps, "create_loupe", "")).not.toBe("");
    expect(loupeBlockedReason(caps, "create_loupe", "observed-1")).toBe("");
  });
  it("requires official Louper and service license setup for cloupe generation", () => {
    expect(
      loupeBlockedReason(
        { ...caps, runtime: { ...caps.runtime, license_ready: false } },
        "create_loupe",
        "observed-1",
      ),
    ).not.toBe("");
    expect(
      loupeBlockedReason(
        { ...caps, runtime: { ...caps.runtime, louper: null } },
        "create_loupe",
        "observed-1",
      ),
    ).not.toBe("");
  });
  it("does not execute administrator setup through the frontend", () => {
    expect(
      loupeBlockedReason(
        { ...caps, operations: [{ function: "setup", available: true }] },
        "setup",
        "observed-1",
      ),
    ).not.toBe("");
  });
  it("does not assume image generation is part of loupeR", () => {
    expect(loupeBlockedReason(caps, "render_projection", "observed-1")).not.toBe("");
    expect(caps.image_formats).toEqual([]);
  });
  it("rejects generic or incompatible service manifests", () => {
    expect(LoupeCapabilitiesSchema.safeParse({ status: "healthy" }).success).toBe(false);
    expect(LoupeCapabilitiesSchema.safeParse({ ...caps, contract_version: 2 }).success).toBe(false);
  });
  it("keeps output names and artifact identifiers from becoming filesystem paths", () => {
    expect(safeOutputName("sample-A.cloupe")).toBe("sample-A");
    expect(() => safeOutputName("../../sample")).toThrow();
    expect(loupeArtifactPath("../artifact?token=example")).toBe(
      "/api/loupe/artifacts/..%2Fartifact%3Ftoken%3Dexample",
    );
  });
  it("rechecks capabilities and sends observed-data-only jobs to the selected service", async () => {
    saveApiConnection("https://scientific.example");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(Response.json(caps))
      .mockResolvedValueOnce(Response.json(run));
    vi.stubGlobal("fetch", fetchMock);
    expect(
      await mbsi.loupe.run({
        dataset_id: "observed-1",
        function: "create_loupe",
        params: { output_name: "sample-A", metadata_cols: ["condition"] },
        allow_demo: false,
      }),
    ).toEqual(run);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://scientific.example/api/loupe/capabilities");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("https://scientific.example/api/loupe/run");
    expect(JSON.parse(fetchMock.mock.calls[1]?.[1]?.body as string)).toEqual({
      dataset_id: "observed-1",
      function: "create_loupe",
      params: { output_name: "sample-A", metadata_cols: ["condition"] },
      allow_demo: false,
    });
  });
  it("does not submit an unavailable function even if called outside the UI", async () => {
    saveApiConnection("https://scientific.example");
    const fetchMock = vi.fn().mockResolvedValue(Response.json(caps));
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      mbsi.loupe.run({
        dataset_id: "observed-1",
        function: "render_projection",
        params: {},
        allow_demo: false,
      }),
    ).rejects.toThrow("not enabled");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("rejects a returned result for another dataset", async () => {
    saveApiConnection("https://scientific.example");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(Response.json(caps))
        .mockResolvedValueOnce(Response.json({ ...run, dataset_id: "other-dataset" })),
    );
    await expect(
      mbsi.loupe.run({
        dataset_id: "observed-1",
        function: "create_loupe",
        params: {},
        allow_demo: false,
      }),
    ).rejects.toThrow("different dataset");
  });
  it("downloads only artifact bytes from the selected scientific service", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("observed artifact", {
        headers: { "content-type": "application/octet-stream" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const blob = await mbsi.loupe.download("result-1", "https://scientific.example");
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "https://scientific.example/api/loupe/artifacts/result-1",
    );
    expect(await blob.text()).toBe("observed artifact");
  });
});
