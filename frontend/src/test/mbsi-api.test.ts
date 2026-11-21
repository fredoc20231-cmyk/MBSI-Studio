import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { checkMbsiConnection, mbsi } from "@/lib/mbsi-api";
import { normalizeApiUrl, resolveApiUrl, saveApiConnection } from "@/lib/mbsi-connection";

const health = { status: "healthy", version: "0.3.0", milestone_1_platforms: ["visium", "xenium"] };

describe("existing MBSI backend connection", () => {
  beforeEach(() => sessionStorage.clear());
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it("uses localhost only in local development, never in a hosted preview", () => {
    expect(resolveApiUrl(undefined, "localhost")).toBe("http://localhost:8000");
    expect(resolveApiUrl("", "mbsi-studio.cronus.life")).toBe("");
    expect(resolveApiUrl(undefined, "spatial-omics-studio.lovable.app")).toBe("");
    expect(resolveApiUrl("https://service.example/", "mbsi-studio.cronus.life")).toBe(
      "https://service.example",
    );
  });

  it("requires HTTPS in the hosted app and strips a copied health/docs suffix", () => {
    expect(normalizeApiUrl("https://service.example/api/health")).toBe("https://service.example");
    expect(normalizeApiUrl("https://service.example/mbsi/docs")).toBe(
      "https://service.example/mbsi",
    );
    expect(() => normalizeApiUrl("http://service.example", "https:")).toThrow("HTTPS");
    expect(() => normalizeApiUrl("https://user:password@service.example")).toThrow("credentials");
  });

  it("checks the repository's observed health response without claiming a generic web page is connected", async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json(health));
    vi.stubGlobal("fetch", fetchMock);
    expect(await checkMbsiConnection("https://service.example")).toEqual(health);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("https://service.example/api/health");
    const headers = fetchMock.mock.calls[0]?.[1]?.headers as Headers;
    expect(headers.has("Content-Type")).toBe(false);
    fetchMock.mockResolvedValue(Response.json({ status: "ok" }));
    await expect(checkMbsiConnection("https://service.example")).rejects.toThrow("health response");
  });

  it("routes uploads, workflow runs and result reads to the selected existing service", async () => {
    saveApiConnection("https://service.example");
    const fetchMock = vi
      .fn()
      .mockImplementation(async () => Response.json({ dataset_id: "observed-dataset" }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["gene,spot1\nGENE1,5\n"], "sample.csv", { type: "text/csv" });
    await mbsi.upload(file, { sample_id: "Sample A" });
    const [uploadUrl, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(uploadUrl).toBe("https://service.example/api/dataset/upload?sample_id=Sample+A");
    expect((init.body as FormData).get("file")).toBe(file);
    expect((init.headers as Headers).has("Content-Type")).toBe(false);
    await mbsi.runWorkflow({
      dataset_id: "observed-dataset",
      module: "spatial_analysis",
      params: {},
      allow_demo: false,
    });
    expect(fetchMock.mock.calls[1]?.[0]).toBe("https://service.example/api/workflow/run");
    expect(JSON.parse(fetchMock.mock.calls[1]?.[1]?.body as string).allow_demo).toBe(false);
    await mbsi.results("observed-dataset");
    expect(fetchMock.mock.calls[2]?.[0]).toBe(
      "https://service.example/api/results/list?dataset_id=observed-dataset",
    );
  });

  it("preserves the scientific backend's rejection reason", async () => {
    saveApiConnection("https://service.example");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response('{"detail":"Unsupported FASTQ input"}', { status: 422 })),
    );
    await expect(mbsi.upload(new File(["data"], "reads.fastq"), {})).rejects.toThrow(
      '[422] {"detail":"Unsupported FASTQ input"}',
    );
  });
});
