import { createFileRoute } from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronLeft,
  Columns2,
  Grid2X2,
  Image,
  LayoutGrid,
  Maximize2,
  Minus,
  Plus,
  Scan,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { mbsi, type DatasetSummary, type SpatialResponse } from "@/lib/mbsi-api";
import { EmptyState, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Explore spatial tissue maps — MBSI Studio" },
      {
        name: "description",
        content:
          "Explore spatial transcriptomics samples, tissue maps, gene expression and cellular neighborhoods in MBSI Studio.",
      },
      { property: "og:title", content: "Explore spatial tissue maps — MBSI Studio" },
      {
        property: "og:description",
        content:
          "An integrated workspace for spatial tissue maps, gene expression and sample comparison.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Explore,
});

const VIEW_TABS = [
  "Spatial",
  "Feature Plot",
  "Cluster",
  "Domain",
  "Niche",
  "Interaction",
  "Trajectory",
];

const PALETTE = ["#22577A", "#38A3A5", "#D89A36", "#B25B7D", "#4F8D42", "#764FA5", "#D04B42"];

function SpatialScatter({ data, zoom }: { data: SpatialResponse; zoom: number }) {
  const points = data.points;
  if (points.length === 0) {
    return <p className="py-12 text-center text-sm text-muted-foreground">No observed spatial points were returned.</p>;
  }
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  const width = Math.max(1, maxX - minX);
  const height = Math.max(1, maxY - minY);
  const pad = Math.max(width, height) * 0.04;
  const spanX = (width + pad * 2) / zoom;
  const spanY = (height + pad * 2) / zoom;
  const viewX = (minX + maxX - spanX) / 2;
  const viewY = (minY + maxY - spanY) / 2;
  const radius = Math.max(width, height) / 200;
  const values = points.map((point) => Number(point.value)).filter((n) => Number.isFinite(n));
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const categories = Array.from(new Set(points.map((point) => String(point.value)))).sort();
  const color = (value: number | string): string => {
    if (data.categorical) return PALETTE[Math.max(0, categories.indexOf(String(value))) % PALETTE.length];
    const t = (Number(value) - min) / (max - min || 1);
    return "hsl(" + String(Math.round(220 - t * 220)) + " 75% 45%)";
  };
  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="min-h-0 flex-1 overflow-hidden rounded-lg border border-border bg-background">
        <svg
          className="h-full min-h-64 w-full"
          viewBox={[viewX, viewY, spanX, spanY].join(" ")}
          preserveAspectRatio="xMidYMid meet"
          role="img"
          aria-label={"Observed spatial values for " + data.feature}
        >
          {points.map((point) => (
            <circle key={point.barcode} cx={point.x} cy={point.y} r={radius}
                    fill={color(point.value)} fillOpacity="0.9">
              <title>{point.barcode + ": " + String(point.value)}</title>
            </circle>
          ))}
        </svg>
      </div>
      <p className="text-[11px] text-muted-foreground">
        {"Observed " + data.feature + " · " + data.returned_observations + "/" +
          data.total_observations + " spots · " + data.source_layer +
          (data.downsampled ? " · downsampled display" : "")}
      </p>
      <div className="flex flex-wrap gap-2 text-[10px] text-muted-foreground">
        {data.categorical
          ? categories.slice(0, 12).map((cat) => (
              <span key={cat} className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color(cat) }} />{cat}
              </span>
            ))
          : <span>{"Range: " + min.toFixed(2) + " – " + max.toFixed(2)}</span>}
      </div>
    </div>
  );
}

function Explore() {
  const [activeTab, setActiveTab] = useState("Spatial");
  const [grouping, setGrouping] = useState("By Sample");
  const [datasetId, setDatasetId] = useState("");
  const [geneSearch, setGeneSearch] = useState("");
  const [selectedGene, setSelectedGene] = useState("");
  const [zoom, setZoom] = useState(1);
  const datasetsQuery = useQuery<DatasetSummary[]>({
    queryKey: ["uploaded-datasets"],
    queryFn: async () => (await mbsi.datasets()).datasets,
    retry: 1,
  });
  const datasets = datasetsQuery.data ?? [];
  useEffect(() => {
    if (!datasetId && datasets.length > 0) setDatasetId(datasets[0].dataset_id);
  }, [datasetId, datasets]);
  const featuresQuery = useQuery({
    queryKey: ["features", datasetId, geneSearch],
    queryFn: () => mbsi.features(datasetId, geneSearch),
    enabled: Boolean(datasetId),
  });
  const availableGenes = featuresQuery.data?.genes ?? [];
  const gene = selectedGene || availableGenes[0] || "";
  const annotations = featuresQuery.data?.annotations ?? [];
  const annotation = activeTab === "Cluster"
    ? (["cluster", "leiden"].find((key) => annotations.includes(key)) || "")
    : activeTab === "Domain"
      ? (["domain"].find((key) => annotations.includes(key)) || "")
      : activeTab === "Niche"
        ? (["niche", "spatial_niche"].find((key) => annotations.includes(key)) || "")
        : "";
  const useAnnotation = ["Cluster", "Domain", "Niche"].includes(activeTab);
  const supported = !["Interaction", "Trajectory"].includes(activeTab);
  const canQuery = Boolean(datasetId && supported && (useAnnotation ? annotation : gene));
  const spatialQuery = useQuery({
    queryKey: ["spatial", datasetId, activeTab, gene, annotation],
    queryFn: () => mbsi.spatial(datasetId, useAnnotation ? { annotation } : { gene }),
    enabled: canQuery,
    retry: false,
  });

  return (
    <Workspace>
      <h1 className="sr-only">Explore spatial tissue maps</h1>
      <div className="flex h-full min-h-[520px] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-panel">
        <div
          className="scrollbar-thin flex h-12 shrink-0 items-end gap-6 overflow-x-auto border-b border-border px-4"
          role="tablist"
          aria-label="Spatial visualizations"
        >
          {VIEW_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`relative h-12 shrink-0 text-[13px] font-medium after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:rounded-t-full after:bg-primary after:transition-transform ${
                activeTab === tab
                  ? "text-primary after:scale-x-100"
                  : "text-muted-foreground after:scale-x-0 hover:text-foreground"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-1 2xl:grid-cols-[minmax(0,1.18fr)_minmax(330px,0.82fr)]">
          <section
            aria-label={`${activeTab} tissue canvas`}
            className="flex min-h-[420px] min-w-0 flex-col border-b border-border 2xl:border-b-0 2xl:border-r"
          >
            <div className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-3">
              <div className="flex min-w-0 items-center gap-2">
                <button
                  type="button"
                  aria-label="Previous sample"
                  disabled={datasets.length < 2}
                  onClick={() => {
                    const index = datasets.findIndex((item) => item.dataset_id === datasetId);
                    setDatasetId(datasets[(index - 1 + datasets.length) % datasets.length].dataset_id);
                    setSelectedGene("");
                  }}
                  className="rounded-md border border-border p-1.5 text-muted-foreground disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <div className="relative min-w-0">
                  <select
                    aria-label="Selected sample"
                    className="h-8 w-48 max-w-full appearance-none rounded-lg border border-input bg-background px-3 pr-8 text-xs text-foreground outline-none"
                    value={datasetId}
                    onChange={(event) => { setDatasetId(event.target.value); setSelectedGene(""); setZoom(1); }}
                  >
                    <option value="">Select sample</option>
                    {datasets.map((dataset) => (
                      <option key={dataset.dataset_id} value={dataset.dataset_id}>
                        {dataset.sample_id || dataset.dataset_id.slice(0, 12)}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-2 top-2 h-4 w-4 text-muted-foreground" />
                </div>
              </div>
              <div className="flex items-center gap-1">
                {[Scan, Minus, Plus].map((Icon, index) => (
                  <button
                    key={index}
                    type="button"
                    aria-label={["Fit tissue", "Zoom out", "Zoom in"][index]}
                    onClick={() => setZoom((old) => index === 0 ? 1 : index === 1 ? Math.max(1, old / 1.4) : Math.min(8, old * 1.4))}
                    disabled={!spatialQuery.data}
                    className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted disabled:opacity-40"
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                ))}
              </div>
            </div>
            <div className="flex min-h-0 flex-1 flex-col gap-3 p-3">
              {datasetId && supported && !useAnnotation && (
                <div className="flex flex-wrap gap-2">
                  <input
                    aria-label="Search genes"
                    placeholder="Filter genes"
                    value={geneSearch}
                    onChange={(event) => { setGeneSearch(event.target.value); setSelectedGene(""); }}
                    className="h-8 min-w-32 flex-1 rounded-lg border border-input bg-background px-3 text-xs"
                  />
                  <select
                    aria-label="Gene to display"
                    value={gene}
                    onChange={(event) => setSelectedGene(event.target.value)}
                    className="h-8 min-w-32 flex-1 rounded-lg border border-input bg-background px-2 text-xs"
                  >
                    {availableGenes.length === 0 && <option value="">No matching genes</option>}
                    {availableGenes.map((feature) => <option key={feature} value={feature}>{feature}</option>)}
                  </select>
                </div>
              )}
              {spatialQuery.isPending && canQuery ? (
                <p className="py-8 text-center text-sm text-muted-foreground">Loading observed spatial values…</p>
              ) : spatialQuery.isError && canQuery ? (
                <p role="alert" className="py-8 text-center text-sm text-destructive">
                  {"Unable to display spatial data: " + (spatialQuery.error as Error).message}
                </p>
              ) : canQuery && spatialQuery.data ? (
                <SpatialScatter data={spatialQuery.data} zoom={zoom} />
              ) : (
                <EmptyState
                  title={supported ? "No observed spatial layer available" : "Analysis not yet available"}
                  body={datasetsQuery.isError
                    ? "Unable to connect to the scientific backend. Check the Render deployment and API URL."
                    : !datasetId
                      ? "Upload a supported Visium or Xenium dataset to explore observed coordinates."
                      : useAnnotation
                        ? "This dataset does not contain a computed annotation for the selected view."
                        : supported
                          ? "No gene is available for this dataset."
                          : "This view requires a validated analysis output from the backend."}
                  icon={<Image className="h-6 w-6" strokeWidth={1.5} />}
                  action={!datasetId ? <UploadButton label="Upload spatial dataset" /> : undefined}
                />
              )}
            </div>
          </section>

          <section aria-label="Sample comparison" className="flex min-h-[360px] min-w-0 flex-col">
            <div className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-4">
              <div
                className="flex h-full items-end gap-5"
                role="tablist"
                aria-label="Comparison grouping"
              >
                {["By Sample", "By Condition"].map((item) => (
                  <button
                    key={item}
                    type="button"
                    role="tab"
                    aria-selected={grouping === item}
                    onClick={() => setGrouping(item)}
                    className={`relative h-full text-xs font-medium after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary ${grouping === item ? "text-primary after:scale-x-100" : "text-muted-foreground after:scale-x-0"}`}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                {[Grid2X2, Columns2, LayoutGrid].map((Icon, index) => (
                  <button
                    key={index}
                    type="button"
                    aria-label={["Two-column grid", "Single-column grid", "Compact grid"][index]}
                    className={`rounded-md p-1.5 hover:bg-muted ${index === 0 ? "bg-accent text-primary" : ""}`}
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                ))}
              </div>
            </div>
            <div className="grid min-h-0 flex-1 grid-cols-2 gap-2 p-3">
              {datasets.slice(0, 4).map((dataset) => (
                <div
                  key={dataset.dataset_id}
                  className="flex min-h-32 flex-col overflow-hidden rounded-lg border border-border bg-card"
                >
                  <div className="border-b border-border px-3 py-2 text-left text-[11px] font-medium text-muted-foreground">
                    {dataset.sample_id || dataset.dataset_id.slice(0, 15)}
                  </div>
                  <div className="map-grid flex flex-1 flex-col items-center justify-center bg-panel-subtle/35 p-3 text-center text-muted-foreground">
                    <Image className="mb-2 h-6 w-6" strokeWidth={1.3} />
                    <span className="text-[10px]">{String(dataset.readiness?.status ?? "unverified")}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </Workspace>
  );
}
