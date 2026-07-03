/**
 * MBSI-Studio ↔ AIStudio API contract.
 *
 * TypeScript interfaces matching the FastAPI backend (mbsi.api.app) exactly.
 * Generated from mbsi/api/aistudio.py. Do not add fields the backend does not
 * return — these shapes are the single source of truth for the frontend.
 *
 * Base URL: read from VITE_API_BASE_URL (default "http://localhost:8000").
 */

/* ------------------------------------------------------------------ *
 * GET /api/technologies/frontend  ->  { technologies: Technology[] }
 * ------------------------------------------------------------------ */
export interface Technology {
  id: string;                       // e.g. "visium"
  key: string;                      // same as id (back-compat)
  name: string;                     // "10x Visium"
  resolution: string;               // "55 µm spots"  (StudySetupView reads this)
  type: string;                     // "Sequencing-based" | "Imaging-based" | "Generic"
  modality: string;                 // alias of `type`
  milestone_functional: boolean;    // true = full ingest+analysis available now
  milestone_status: string;         // "active" | "coming_later"
  required_files: string[];
  optional_files: string[];
  supports_images: boolean;
  supports_segmentation: boolean;
  supports_cells: boolean;
  supports_bins: boolean;
  normalization: string;
  clustering: string[];
  compatible_analyses: string[];
  notes: string;
}

export interface TechnologiesResponse {
  technologies: Technology[];
}

/* ------------------------------------------------------------------ *
 * GET /api/projects/{projectId}/spatial-data
 *   query: dataset_id, genes (comma-sep), max_cells=5000, max_genes=12
 * ------------------------------------------------------------------ */
export interface SpatialCell {
  id: string;
  x: number;
  y: number;
  cluster: number;
  total_counts: number;
  n_genes_by_counts: number;
  pct_counts_mt: number;
  expression: Record<string, number>;            // raw (log-layer) value per gene in genesList
  normalizedExpression: Record<string, number>;  // log1p CP10k per gene
}

export interface Validation {
  name: string;
  status: "passed" | "warning" | "failed";
  message: string;
}

export interface SpatialDataPayload {
  technology: string;
  matrixDimensions: string;        // "1,289 cells x 21,066 genes"
  detectedCellsCount: number;
  detectedGenesCount: number;
  mitochondrialRatio: string;      // "0.17%"
  qcScore: number;                 // 0-100
  histologyImageUrl: string;
  genesList: string[];             // genes embedded per-cell
  cells: SpatialCell[];            // subsampled to max_cells
  validations: Validation[];
  warnings: string[];
  error?: string;                  // present only on failure (dataset not found, etc.)
}

/* ------------------------------------------------------------------ *
 * POST /api/upload/sign   body: { filename, contentType }
 * ------------------------------------------------------------------ */
export interface UploadSignRequest {
  filename: string;
  contentType?: string;
}

export interface UploadSignResponse {
  uploadId: string;
  mode: "direct" | "signed";       // "direct" when no cloud bucket configured
  uploadUrl: string;               // "/api/dataset/upload" for direct mode
  method: string;                  // "POST"
  fields: Record<string, string>;
  objectKey: string;
  expiresIn: number;
  note: string;
}

/* ------------------------------------------------------------------ *
 * GET /api/jobs/{jobId}/status
 * ------------------------------------------------------------------ */
export type JobState = "processing" | "completed" | "failed" | "not_found" | string;

export interface JobStatus {
  jobId: string;
  status: JobState;
  module: string;
  outputs: Record<string, unknown>;
  warnings: string[];
}

/* ------------------------------------------------------------------ *
 * POST /api/workflow/run   ->  { run_id, status, ... }
 * (Expert mode passes params; novice mode omits them.)
 * ------------------------------------------------------------------ */
export interface WorkflowRunRequest {
  dataset_id: string;
  module?: string;                 // "qc" | "analyze" | "svg" | "mbsi" | ...
  params?: Record<string, unknown>;
}

export interface WorkflowRunResponse {
  run_id: string;
  status: string;
  module: string;
  outputs: Record<string, unknown>;
  warnings: string[];
}
