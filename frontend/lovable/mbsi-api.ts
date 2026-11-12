/** Typed API client for a Lovable-generated React frontend.
 * No browser-side biology calculations and no mock production results.
 */
export type PlatformStatus = "existing_ingestion" | "existing_ingestion_and_comparisons"
  | "preview" | "adapter_required" | "experimental_adapter"
  | "not_implemented_in_v2_preview";

export interface MBSICapabilities {
  product: string;
  api_version: string;
  mode: string;
  real_data_only: boolean;
  supports: Record<string, PlatformStatus | string>;
  requirements: string[];
}

export interface SampleSummary {
  dataset_id: string;
  observations: number;
  genes: number;
  annotation_columns: string[];
  spatial_available: boolean;
  platform: string;
  expression_space: string;
}

export interface SpatialPoint {
  x: number;
  y: number;
  annotation: string;
  expression?: number;
}

export interface SpatialPointResponse {
  dataset_id: string;
  annotation: string;
  gene: string | null;
  observation_count: number;
  returned_count: number;
  sampling: string;
  coordinate_units: string;
  points: SpatialPoint[];
}

export interface ComparisonRequest {
  reference_dataset_id: string;
  comparison_dataset_id: string;
  reference_annotation: string;
  comparison_annotation: string;
  genes: string[];
  include_similarity?: boolean;
}

export interface CompositionRow {
  population: string;
  sample_id_a?: string;
  sample_id_b?: string;
  n_units_a: number;
  n_units_b: number;
  fraction_a: number;
  fraction_b: number;
  delta_fraction: number;
}

export interface ExpressionRow {
  population: string;
  gene: string;
  sample_id_a: string;
  sample_id_b: string;
  mean_expression_a: number;
  mean_expression_b: number;
  n_units_a: number;
  n_units_b: number;
  delta_mean: number;
}

export interface ComparisonResult {
  status: "descriptive_only";
  reference_dataset_id: string;
  comparison_dataset_id: string;
  composition: CompositionRow[];
  expression: ExpressionRow[];
  cluster_similarity: null | {
    reference_labels: string[];
    comparison_labels: string[];
    values: number[][];
  };
  warnings: string[];
  provenance: {
    method: string;
    inference: "none";
    normalization: string;
    comparison_unit: string;
  };
}

const API_BASE_URL = (
  import.meta.env.VITE_MBSI_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export class MBSIApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "MBSIApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(API_BASE_URL + path, {
    ...init,
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init.headers || {}),
    },
  });
  if (!response.ok) {
    let message = "MBSI API error " + response.status;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      // Preserve HTTP status without displaying a fabricated response.
    }
    throw new MBSIApiError(response.status, message);
  }
  return (await response.json()) as T;
}

export const mbsi = {
  health: () => request<{ status: string }>("/api/health"),
  capabilities: () => request<MBSICapabilities>("/api/v2/capabilities"),
  sample: (id: string) =>
    request<SampleSummary>("/api/v2/datasets/" + encodeURIComponent(id) + "/summary"),
  genes: (id: string, query = "", limit = 100) =>
    request<{ dataset_id: string; genes: string[]; total_matches: number }>(
      "/api/v2/datasets/" + encodeURIComponent(id) + "/genes?" +
      new URLSearchParams({query, limit: String(limit)}).toString()
    ),
  spatialPoints: (id: string, annotation: string, gene?: string, limit = 10000) =>
    request<SpatialPointResponse>(
      "/api/v2/datasets/" + encodeURIComponent(id) + "/spatial-points?" +
      new URLSearchParams({
        annotation,
        ...(gene ? {gene} : {}),
        limit: String(limit),
      }).toString()
    ),
  compare: (body: ComparisonRequest) =>
    request<ComparisonResult>("/api/v2/comparisons/preview", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  upload: (file: File, sampleId: string, technologyHint: string, projectId = "") => {
    const form = new FormData();
    form.append("file", file);
    const params = new URLSearchParams({
      project_id: projectId,
      sample_id: sampleId,
      technology_hint: technologyHint,
    });
    return request<{
      dataset_id: string;
      platform: string;
      readiness: Record<string, unknown>;
      warnings: string[];
      summary: Record<string, unknown>;
    }>("/api/dataset/upload?" + params.toString(), {
      method: "POST",
      body: form,
    });
  },
};
