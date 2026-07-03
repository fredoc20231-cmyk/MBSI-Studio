/**
 * MBSI-Studio API client for the AIStudio frontend.
 * One typed function per backend endpoint. Import types from ./mbsi_contract.
 */
import type {
  TechnologiesResponse,
  SpatialDataPayload,
  UploadSignRequest,
  UploadSignResponse,
  JobStatus,
  WorkflowRunRequest,
  WorkflowRunResponse,
} from "./mbsi_contract";

const BASE =
  (import.meta as any)?.env?.VITE_API_BASE_URL ?? "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json() as Promise<T>;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json() as Promise<T>;
}

/** Technology dropdown — every item is guaranteed to carry resolution + type. */
export function listTechnologies(): Promise<TechnologiesResponse> {
  return getJSON<TechnologiesResponse>("/api/technologies/frontend");
}

/** Main spatial payload for TissueCanvas. */
export function getSpatialData(
  projectId: string,
  opts: { datasetId?: string; genes?: string[]; maxCells?: number; maxGenes?: number } = {}
): Promise<SpatialDataPayload> {
  const q = new URLSearchParams();
  if (opts.datasetId) q.set("dataset_id", opts.datasetId);
  if (opts.genes?.length) q.set("genes", opts.genes.join(","));
  if (opts.maxCells) q.set("max_cells", String(opts.maxCells));
  if (opts.maxGenes) q.set("max_genes", String(opts.maxGenes));
  const qs = q.toString();
  return getJSON<SpatialDataPayload>(
    `/api/projects/${encodeURIComponent(projectId)}/spatial-data${qs ? "?" + qs : ""}`
  );
}

/** Request an upload descriptor, then upload the file (handles direct-mode fallback). */
export async function uploadDataset(
  file: File,
  meta: { projectId: string; technologyHint?: string; sampleId?: string }
): Promise<Response> {
  const sign = await postJSON<UploadSignResponse>("/api/upload/sign", {
    filename: file.name,
    contentType: file.type || "application/octet-stream",
  } as UploadSignRequest);

  if (sign.mode === "signed") {
    return fetch(sign.uploadUrl, { method: "PUT", body: file });
  }
  // direct multipart POST to /api/dataset/upload
  const form = new FormData();
  form.append("file", file);
  const q = new URLSearchParams({
    project_id: meta.projectId,
    sample_id: meta.sampleId ?? "",
  });
  if (meta.technologyHint) q.set("technology_hint", meta.technologyHint);
  return fetch(`${BASE}${sign.uploadUrl}?${q.toString()}`, {
    method: "POST",
    body: form,
  });
}

/** Kick off analysis. Novice: omit params. Expert: pass module + params. */
export function runWorkflow(req: WorkflowRunRequest): Promise<WorkflowRunResponse> {
  return postJSON<WorkflowRunResponse>("/api/workflow/run", req);
}

/** Poll job status until terminal. */
export function getJobStatus(jobId: string): Promise<JobStatus> {
  return getJSON<JobStatus>(`/api/jobs/${encodeURIComponent(jobId)}/status`);
}

/** Convenience: poll every intervalMs until completed/failed/not_found. */
export async function pollJob(
  jobId: string,
  onTick?: (s: JobStatus) => void,
  intervalMs = 2000,
  timeoutMs = 600000
): Promise<JobStatus> {
  const start = Date.now();
  while (true) {
    const s = await getJobStatus(jobId);
    onTick?.(s);
    if (["completed", "failed", "not_found"].includes(s.status)) return s;
    if (Date.now() - start > timeoutMs) return { ...s, status: "failed" };
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
