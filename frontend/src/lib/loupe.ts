import { z } from "zod";

// Capability descriptions only. No loupeR source or scientific computation is bundled.
export const LOUPE_FUNCTIONS = [
  {
    name: "create_loupe_from_seurat",
    label: "Seurat → Loupe",
    group: "Export",
    needsLicense: true,
  },
  { name: "create_loupe", label: "Counts → Loupe", group: "Export", needsLicense: true },
  { name: "create_hdf5", label: "HDF5 interchange", group: "Export", needsLicense: false },
  { name: "select_assay", label: "Select usable assay", group: "Selection", needsLicense: false },
  {
    name: "counts_matrix_from_assay",
    label: "Extract counts",
    group: "Selection",
    needsLicense: false,
  },
  {
    name: "select_clusters",
    label: "Select cluster categories",
    group: "Selection",
    needsLicense: false,
  },
  {
    name: "select_projections",
    label: "Select 2D projections",
    group: "Selection",
    needsLicense: false,
  },
  {
    name: "read_feature_ids_from_tsv",
    label: "Read feature IDs",
    group: "Selection",
    needsLicense: false,
  },
  {
    name: "validate_count_mat",
    label: "Validate count matrix",
    group: "Validation",
    needsLicense: false,
  },
  {
    name: "validate_barcodes",
    label: "Validate barcodes",
    group: "Validation",
    needsLicense: false,
  },
  {
    name: "validate_clusters",
    label: "Validate clusters",
    group: "Validation",
    needsLicense: false,
  },
  {
    name: "validate_projections",
    label: "Validate projections",
    group: "Validation",
    needsLicense: false,
  },
  {
    name: "create_bugreport",
    label: "Count-matrix diagnostics",
    group: "Diagnostics",
    needsLicense: false,
  },
  {
    name: "create_bugreport_from_seurat",
    label: "Seurat diagnostics",
    group: "Diagnostics",
    needsLicense: false,
  },
  { name: "setup", label: "Runtime & license setup", group: "Service", needsLicense: false },
] as const;

// setup is one of the 15 public exports; it is an administrator-only service operation.
export const LoupeCapabilitiesSchema = z.object({
  contract_version: z.literal(1),
  runtime: z.object({
    r: z.string().nullable(),
    loupeR: z.string().nullable(),
    hdf5: z.string().nullable(),
    louper: z.string().nullable(),
    license_ready: z.boolean(),
  }),
  operations: z.array(
    z.object({ function: z.string(), available: z.boolean(), reason: z.string().optional() }),
  ),
  image_formats: z.array(z.enum(["png", "svg"])),
});
export type LoupeCapabilities = z.infer<typeof LoupeCapabilitiesSchema>;
export const LoupeArtifactSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  kind: z.enum(["cloupe", "hdf5", "image", "report", "table"]),
  mime_type: z.string(),
});
export const LoupeRunSchema = z.object({
  id: z.string().min(1),
  dataset_id: z.string().min(1),
  function: z.string(),
  status: z.enum(["queued", "running", "completed", "blocked", "failed"]),
  outputs: z.record(z.unknown()),
  warnings: z.array(z.string()),
  artifacts: z.array(LoupeArtifactSchema),
  error: z.string().optional(),
});
export type LoupeRun = z.infer<typeof LoupeRunSchema>;
export type LoupeArtifact = z.infer<typeof LoupeArtifactSchema>;
export type LoupeRequest = {
  dataset_id: string;
  function: string;
  params: Record<string, unknown>;
  allow_demo: false;
};

export function loupeBlockedReason(
  caps: LoupeCapabilities | undefined,
  fn: string,
  datasetId: string,
): string {
  if (!caps) return "Loupe is not available on the connected scientific service.";
  if (fn === "setup")
    return "Service administrator must install the official converter and complete 10x license setup.";
  if (!datasetId) return "Select an observed dataset.";
  const operation = caps.operations.find((item) => item.function === fn);
  if (!operation?.available)
    return operation?.reason || "This function is not enabled on the scientific service.";
  const needsLicense = LOUPE_FUNCTIONS.find((item) => item.name === fn)?.needsLicense;
  if (needsLicense && (!caps.runtime.license_ready || !caps.runtime.louper))
    return "The official Louper converter and completed service license setup are required.";
  return "";
}

export function loupeArtifactPath(id: string): string {
  return `/api/loupe/artifacts/${encodeURIComponent(id)}`;
}

export function safeOutputName(value: string): string {
  const name = value.trim().replace(/\.(cloupe|h5|hdf5|png|svg)$/i, "");
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,99}$/.test(name) || name.includes(".."))
    throw new Error(
      "Use a filename of 1–100 letters, numbers, dots, underscores or hyphens, without paths.",
    );
  return name;
}
