// Typed client for the MBSI FastAPI backend (single source of truth: mbsi.api.app:app).
// Regenerate full types from <API>/openapi.json with openapi-typescript when available.
import { getApiUrl, isMbsiHealth } from "@/lib/mbsi-connection";
import {
  LoupeCapabilitiesSchema,
  LoupeRunSchema,
  loupeArtifactPath,
  loupeBlockedReason,
  type LoupeRequest,
} from "@/lib/loupe";

export { getApiUrl } from "@/lib/mbsi-connection";

async function responseJson<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`[${res.status}] ${await res.text()}`);
  if (!res.headers.get("content-type")?.includes("application/json")) {
    throw new Error("The service returned a web page instead of MBSI data. Check its address.");
  }
  return res.json() as Promise<T>;
}

async function req<T>(path: string, init?: RequestInit, baseUrl = getApiUrl()): Promise<T> {
  if (!baseUrl) {
    throw new Error(
      "No scientific service connected. Open Scientific backend to connect the running MBSI service.",
    );
  }
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  // Do not send JSON headers on GETs or overwrite the multipart file boundary.
  if (typeof init?.body === "string") headers.set("Content-Type", "application/json");
  let res: Response;
  try {
    res = await fetch(`${baseUrl}${path}`, { ...init, headers });
  } catch {
    throw new Error(
      "Cannot reach the MBSI service. Check that it is running and allows this app’s address.",
    );
  }
  return responseJson<T>(res);
}

export async function checkMbsiConnection(baseUrl = getApiUrl()) {
  const health = await req<unknown>("/api/health", { signal: AbortSignal.timeout(10000) }, baseUrl);
  if (!isMbsiHealth(health))
    throw new Error("This address did not return the repository’s MBSI health response.");
  return health;
}

export type EmbeddingRequest = {
  image_ids: string[];
  features: number[][];
  metadata?: Record<string, Record<string, string>>;
  method: "pca" | "tsne";
};
export type EmbeddingPoint = {
  image_id: string;
  x: number;
  y: number;
  platform?: string;
  sample_id?: string;
  [k: string]: unknown;
};
export type EmbeddingResponse = { status: string; source: string; coordinates: EmbeddingPoint[] };

export type DatasetUploadResponse = {
  dataset_id: string;
  adata_path: string;
  platform: string;
  technology_profile: Record<string, unknown>;
  readiness: Record<string, unknown>;
  compatibility: Record<string, unknown>;
  warnings: string[];
  summary: Record<string, unknown>;
};

export type WorkflowRunRequest = {
  project_id?: string;
  dataset_id: string;
  module: string;
  params: Record<string, unknown>;
  allow_demo: false;
};

export type WorkflowRunResponse = {
  run_id: string;
  status: string;
  module: string;
  outputs: Record<string, unknown>;
  warnings: string[];
};

export type ResultsListResponse = {
  dataset_id: string;
  results: Record<string, unknown>[];
};

export type Capability = {
  module: string;
  phase: number;
  label: string;
  evidence_tier: string;
  packages: Record<string, string | null>;
  installed: boolean;
};

export const mbsi = {
  // Optional proposed Loupe v1 contract. Missing endpoints remain unavailable.
  loupe: {
    capabilities: async (signal?: AbortSignal) =>
      LoupeCapabilitiesSchema.parse(
        await req<unknown>("/api/loupe/capabilities", signal ? { signal } : undefined),
      ),
    run: async (body: LoupeRequest, baseUrl = getApiUrl()) => {
      const caps = LoupeCapabilitiesSchema.parse(
        await req<unknown>("/api/loupe/capabilities", undefined, baseUrl),
      );
      const blocked = loupeBlockedReason(caps, body.function, body.dataset_id);
      if (blocked) throw new Error(blocked);
      const result = LoupeRunSchema.parse(
        await req<unknown>(
          "/api/loupe/run",
          {
            method: "POST",
            body: JSON.stringify({ ...body, allow_demo: false }),
          },
          baseUrl,
        ),
      );
      if (result.dataset_id !== body.dataset_id || result.function !== body.function)
        throw new Error(
          "The scientific service returned a run for a different dataset or function.",
        );
      return result;
    },
    status: async (id: string, signal?: AbortSignal) =>
      LoupeRunSchema.parse(
        await req<unknown>(
          `/api/loupe/status?run_id=${encodeURIComponent(id)}`,
          signal ? { signal } : undefined,
        ),
      ),
    runs: async (datasetId: string, signal?: AbortSignal) => {
      const result = await req<unknown>(
        `/api/loupe/runs?dataset_id=${encodeURIComponent(datasetId)}`,
        signal ? { signal } : undefined,
      );
      const parsed = LoupeRunSchema.array().parse(result);
      if (parsed.some((run) => run.dataset_id !== datasetId))
        throw new Error("Results contain a different dataset.");
      return parsed;
    },
    download: async (artifactId: string, baseUrl = getApiUrl()) => {
      if (!baseUrl) throw new Error("No scientific service connected.");
      const response = await fetch(`${baseUrl}${loupeArtifactPath(artifactId)}`, {
        headers: { Accept: "application/octet-stream" },
      });
      if (!response.ok) throw new Error(`[${response.status}] ${await response.text()}`);
      if (response.headers.get("content-type")?.includes("text/html"))
        throw new Error("The service returned a web page instead of an artifact.");
      return response.blob();
    },
  },
  capabilities: () => req<{ modules: Capability[] }>("/api/capabilities"),
  health: () => checkMbsiConnection(),
  technologies: () => req<unknown>("/api/technologies"),
  readiness: (datasetId: string) =>
    req<unknown>(`/api/dataset/readiness?dataset_id=${encodeURIComponent(datasetId)}`),
  results: (datasetId = "default") =>
    req<ResultsListResponse>(`/api/results/list?dataset_id=${encodeURIComponent(datasetId)}`),
  findings: () => req<unknown>("/api/findings/list"),
  evidence: () => req<unknown>("/api/evidence/list"),
  workflowStatus: (runId: string) =>
    req<WorkflowRunResponse>(`/api/workflow/status?run_id=${encodeURIComponent(runId)}`),
  runWorkflow: (body: WorkflowRunRequest) =>
    req<WorkflowRunResponse>("/api/workflow/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  embedding: (body: EmbeddingRequest) =>
    req<EmbeddingResponse>("/api/v1/imaging/embedding", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  upload: (file: File, params: Record<string, string>) => {
    const fd = new FormData();
    fd.append("file", file);
    const q = new URLSearchParams(params).toString();
    return req<DatasetUploadResponse>(`/api/dataset/upload${q ? `?${q}` : ""}`, {
      method: "POST",
      body: fd,
    });
  },
};
