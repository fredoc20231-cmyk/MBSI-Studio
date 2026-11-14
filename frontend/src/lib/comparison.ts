import type { WorkflowRunRequest } from "@/lib/mbsi-api";

export type ComparisonLevel = {
  id: string;
  label: string;
  description: string;
  module?: string;
  params?: Record<string, unknown>;
  detailPaths?: readonly (readonly string[])[];
  unavailableReason?: string;
};

export const COMPARISON_LEVELS = [
  {
    id: "expression",
    label: "Gene expression",
    description:
      "Compare cluster markers and pairwise differential-expression outputs across samples.",
    module: "spatial_analysis",
    params: { workflow_preset: "spatial_transcriptomics" },
    detailPaths: [
      ["seurat_like_results", "de_results"],
      ["seurat_like_results", "markers"],
    ],
  },
  {
    id: "clusters",
    label: "Clusters",
    description: "Compare observed cluster counts, assignments and marker outputs across samples.",
    module: "spatial_analysis",
    params: { workflow_preset: "spatial_transcriptomics" },
    detailPaths: [["seurat_like_results", "markers"]],
  },
  {
    id: "domains",
    label: "Spatial domains",
    description:
      "Run domain detection independently for each selected sample and align its returned summaries.",
    module: "spatial_domains",
    params: { method: "leiden", resolution: 0.8 },
    detailPaths: [["domain_summary"]],
  },
  {
    id: "phenotypes",
    label: "Cell phenotypes",
    description:
      "Compare marker-panel and tumor-microenvironment phenotyping summaries returned for each sample.",
    module: "phenotyping",
    params: { panel: "immune" },
    detailPaths: [["panel_summary"], ["tme_summary"]],
  },
  {
    id: "spatial-stats",
    label: "Spatial statistics",
    description:
      "Compare spatially variable gene tables and autocorrelation statistics across samples.",
    module: "spatial_variable_genes",
    params: { n_top: 500, k: 6 },
    detailPaths: [["svg_table"]],
  },
  {
    id: "niches",
    label: "Niches",
    description: "Compare cellular neighborhood and niche outputs across samples.",
    unavailableReason:
      "The connected API does not expose a niche-analysis workflow. No niche comparison will be simulated in the browser.",
  },
  {
    id: "interactions",
    label: "Cell interactions",
    description: "Compare ligand–receptor and cell-communication outputs across samples.",
    unavailableReason:
      "The connected API does not expose a cell-interaction workflow for dataset comparisons. No interaction scores will be simulated.",
  },
  {
    id: "trajectories",
    label: "Trajectories",
    description: "Compare observed spatial trajectory outputs across samples.",
    unavailableReason:
      "The connected API does not expose a trajectory workflow. No trajectory or pseudotime values will be simulated.",
  },
] as const satisfies readonly ComparisonLevel[];

export function buildComparisonRequests(
  level: ComparisonLevel,
  datasetIds: readonly string[],
): WorkflowRunRequest[] {
  if (!level.module || datasetIds.length < 2) return [];

  return datasetIds.map((datasetId) => ({
    dataset_id: datasetId,
    module: level.module!,
    params: { ...level.params },
    allow_demo: false,
  }));
}

export type ScalarMetricRow = {
  key: string;
  values: Record<string, string | number | boolean | null>;
};

export function alignScalarMetrics(
  runs: readonly { datasetId: string; outputs: Record<string, unknown> }[],
): ScalarMetricRow[] {
  const keys = [
    ...new Set(
      runs.flatMap((run) =>
        Object.entries(run.outputs)
          .filter(
            ([, value]) => value === null || ["string", "number", "boolean"].includes(typeof value),
          )
          .map(([key]) => key),
      ),
    ),
  ];

  return keys.map((key) => ({
    key,
    values: Object.fromEntries(
      runs.map((run) => {
        const value = run.outputs[key];
        return [
          run.datasetId,
          value === null || ["string", "number", "boolean"].includes(typeof value)
            ? (value as string | number | boolean | null)
            : null,
        ];
      }),
    ),
  }));
}

export function getObservedDetails(
  outputs: Record<string, unknown>,
  paths: readonly (readonly string[])[] = [],
): Record<string, unknown> {
  return Object.fromEntries(
    paths.flatMap((path) => {
      const value = path.reduce<unknown>(
        (current, key) =>
          current && typeof current === "object"
            ? (current as Record<string, unknown>)[key]
            : undefined,
        outputs,
      );
      return value === undefined ? [] : [[path.join("."), value]];
    }),
  );
}
