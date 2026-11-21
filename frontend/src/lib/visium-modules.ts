// Frontend descriptions of the backend's Visium capability modules (mbsi/visium_core).
// Availability always comes from GET /api/capabilities; nothing here is a result.
export type VisiumModule = {
  module: string;
  phase: number;
  title: string;
  description: string;
  params: Record<string, unknown>;
};

export const VISIUM_MODULES: VisiumModule[] = [
  { module: "visium_svg", phase: 1, title: "Spatially variable genes", description: "Moran's I on a hex-grid spatial graph with BH-FDR significance.", params: { mode: "moran", fdr_alpha: 0.05, coord_type: "grid" } },
  { module: "visium_neighborhood", phase: 1, title: "Neighborhood statistics", description: "Neighborhood enrichment, co-occurrence, Ripley's L and interaction matrix.", params: { cluster_key: "leiden" } },
  { module: "visium_niches", phase: 2, title: "Spatial domains & niches", description: "Joint expression + spatial graph clustering with neighbor-weight sensitivity.", params: { spatial_weight: 0.3, resolution: 0.8 } },
  { module: "visium_deconvolution", phase: 3, title: "Spot deconvolution", description: "Per-spot cell-type composition against a single-cell reference.", params: { method: "tangram", reference_label_key: "cell_type" } },
  { module: "visium_replicate_de", phase: 4, title: "Replicate-aware DE", description: "Pseudobulk per sample × domain; blocked below 2 replicates per condition.", params: { sample_key: "sample", condition_key: "condition", domain_key: "spatial_niche", min_replicates: 2 } },
  { module: "visium_cci", phase: 5, title: "Cell-cell interaction", description: "Colocalization z-scores and ligand-receptor tests, labelled hypothesis-level.", params: { cluster_key: "spatial_niche", min_colocalization_z: 2 } },
  { module: "visium_hd_bin", phase: 7, title: "Visium HD binning", description: "2 / 8 / 16 µm bins with chunked aggregation and HD-aware QC.", params: { bin_um: 8 } },
];

export const PHASE_NOTES = [
  { phase: 6, title: "Provenance & guardrails", body: "Every run returns applied parameters, tool versions, a code hash, an evidence tier and field-bound caveats." },
  { phase: 8, title: "Validation & benchmarking", body: "Concordance on public 10x datasets is not yet run; results are unbenchmarked." },
];

export function isBlocked(outputs: Record<string, unknown> | undefined) {
  return Boolean(outputs && typeof outputs["blocked_reason"] === "string");
}
