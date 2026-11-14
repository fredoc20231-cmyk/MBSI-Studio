// Typed client for the MBSI FastAPI backend (single source of truth: mbsi.api.app:app).
// Regenerate full types from <API>/openapi.json with openapi-typescript when available.
export const API_URL: string =
  (import.meta.env["VITE_MBSI_API_URL"] as string | undefined) ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`[${res.status}] ${await res.text()}`);
  return res.json() as Promise<T>;
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

export const mbsi = {
  health: () => req<Record<string, unknown>>("/api/health"),
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
    return fetch(`${API_URL}/api/dataset/upload?${q}`, { method: "POST", body: fd }).then(
      async (r) => {
        if (!r.ok) throw new Error(`[${r.status}] ${await r.text()}`);
        return (await r.json()) as DatasetUploadResponse;
      },
    );
  },
};
