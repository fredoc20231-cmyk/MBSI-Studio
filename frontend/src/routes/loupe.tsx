import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  FileArchive,
  ImageIcon,
  LoaderCircle,
  Play,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Workspace, PageHeader, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";
import { LoupeArtifact } from "@/components/mbsi/LoupeArtifact";
import { mbsi, getApiUrl, type DatasetUploadResponse } from "@/lib/mbsi-api";
import { LOUPE_FUNCTIONS, loupeBlockedReason, safeOutputName } from "@/lib/loupe";
import { useMbsiConnection } from "@/hooks/use-mbsi-connection";

export const Route = createFileRoute("/loupe")({
  head: () => ({
    meta: [
      { title: "Loupe exports & outcomes — MBSI Studio" },
      {
        name: "description",
        content:
          "Configure observed-data LoupeR conversions, validation, selections and scientific-service artifacts in MBSI Studio.",
      },
      { property: "og:title", content: "Loupe exports & outcomes — MBSI Studio" },
      {
        property: "og:description",
        content:
          "Capability-checked Loupe export and separate projection image workflows with traceable outcomes.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Loupe,
});

const inputClass =
  "h-9 w-full rounded-md border border-input bg-background px-3 text-xs outline-none focus:ring-2 focus:ring-ring";
const splitKeys = (value: string) =>
  value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

function Loupe() {
  const service = useMbsiConnection();
  const queryClient = useQueryClient();
  const datasets = useQuery<DatasetUploadResponse[]>({
    queryKey: ["uploaded-datasets"],
    queryFn: () => [],
    initialData: [],
    enabled: false,
  }).data;
  const [selectedDataset, setSelectedDataset] = useState("");
  const datasetId =
    datasets.find((d) => d.dataset_id === selectedDataset)?.dataset_id ||
    datasets[0]?.dataset_id ||
    "";
  const [tab, setTab] = useState("Export");
  const [exportFn, setExportFn] = useState("create_loupe_from_seurat");
  const [utilityFn, setUtilityFn] = useState("validate_count_mat");
  const [name, setName] = useState("mbsi-loupe-export");
  const [metadata, setMetadata] = useState("");
  const [projections, setProjections] = useState("");
  const [featureDataset, setFeatureDataset] = useState("");
  const [dedup, setDedup] = useState(false);
  const [format, setFormat] = useState("png");
  const [gene, setGene] = useState("");
  const [width, setWidth] = useState(1600);
  const [height, setHeight] = useState(1200);
  const [latest, setLatest] = useState<{ service: string; dataset: string; id: string }>();
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<{ service: string; dataset: string; message: string }>();
  const caps = useQuery({
    queryKey: ["loupe-capabilities", service],
    queryFn: ({ signal }) => mbsi.loupe.capabilities(signal),
    enabled: Boolean(service),
    retry: false,
  });
  const runs = useQuery({
    queryKey: ["loupe-runs", service, datasetId],
    queryFn: ({ signal }) => mbsi.loupe.runs(datasetId, signal),
    enabled: Boolean(service && caps.isSuccess && datasetId),
    retry: false,
  });
  const runId = latest?.service === service && latest.dataset === datasetId ? latest.id : "";
  const status = useQuery({
    queryKey: ["loupe-status", service, datasetId, runId],
    queryFn: async ({ signal }) => {
      const result = await mbsi.loupe.status(runId, signal);
      if (result.id !== runId || result.dataset_id !== datasetId)
        throw new Error("The service returned a different run.");
      return result;
    },
    enabled: Boolean(runId),
    retry: false,
    refetchInterval: (query) =>
      ["queued", "running"].includes(query.state.data?.status || "") ? 2000 : false,
  });
  const allRuns = status.data
    ? [status.data, ...(runs.data || []).filter((r) => r.id !== status.data.id)]
    : runs.data || [];
  const fn =
    tab === "Images" ? "render_projection" : tab === "Checks & utilities" ? utilityFn : exportFn;
  const blocked =
    loupeBlockedReason(caps.data, fn, datasetId) ||
    (fn === "render_projection" && !caps.data?.image_formats.includes(format as "png" | "svg")
      ? "This image format is not supported by the service."
      : "");
  const inProgress = ["queued", "running"].includes(status.data?.status || "");
  const errorMessage =
    error?.service === service && error.dataset === datasetId ? error.message : "";

  async function execute() {
    if (blocked || busy || inProgress) return;
    const scope = { service, dataset: datasetId };
    setBusy(service);
    setError(undefined);
    try {
      const params: Record<string, unknown> = {
        output_name: safeOutputName(name),
        dedup_clusters: dedup,
      };
      if (metadata.trim()) params["metadata_cols"] = splitKeys(metadata);
      if (projections.trim()) params["projection_names"] = splitKeys(projections);
      if (datasets.some((d) => d.dataset_id === featureDataset))
        params["features_dataset_id"] = featureDataset;
      if (fn === "render_projection")
        Object.assign(params, { format, gene: gene.trim(), width, height });
      const result = await mbsi.loupe.run(
        { dataset_id: datasetId, function: fn, params, allow_demo: false },
        service,
      );
      if (getApiUrl() !== service) return;
      setLatest({ ...scope, id: result.id });
      queryClient.setQueryData(["loupe-status", service, datasetId, result.id], result);
      void queryClient.invalidateQueries({ queryKey: ["loupe-runs", service, datasetId] });
    } catch (e) {
      setError({ ...scope, message: e instanceof Error ? e.message : "Loupe operation failed." });
    } finally {
      setBusy("");
    }
  }

  return (
    <Workspace>
      <PageHeader
        title="Loupe workspace"
        description="LoupeR 1.1.5 · Seurat and count-matrix exports"
        action={<UploadButton />}
      />
      <div className="mb-5 flex flex-wrap items-center gap-2 border-y border-border py-3 text-xs">
        {["Observed dataset", "Validation", "HDF5", "Louper", ".cloupe"].map((step, i) => (
          <span key={step} className="flex items-center gap-2">
            <span className="font-medium">{step}</span>
            {i < 4 && <ArrowRight className="size-3 text-muted-foreground" />}
          </span>
        ))}
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label className="min-w-0 flex-1 text-xs font-medium">
          Dataset
          <select
            aria-label="Loupe dataset"
            className={`${inputClass} mt-1`}
            value={datasetId}
            onChange={(e) => setSelectedDataset(e.target.value)}
          >
            {!datasets.length && <option value="">No accepted dataset</option>}
            {datasets.map((d) => (
              <option key={d.dataset_id} value={d.dataset_id}>
                {d.dataset_id} · {d.platform}
              </option>
            ))}
          </select>
        </label>
        <Button
          variant="outline"
          size="sm"
          className="mt-5"
          onClick={() => {
            void caps.refetch();
            if (datasetId && caps.isSuccess) void runs.refetch();
          }}
          disabled={!service || caps.isFetching}
        >
          <RefreshCw className={caps.isFetching ? "animate-spin" : ""} />
          Check service
        </Button>
      </div>
      {!caps.isSuccess && (
        <div
          role="status"
          className="mb-4 flex gap-3 rounded-lg border border-border bg-panel-subtle p-4"
        >
          <ShieldAlert className="size-5 shrink-0 text-primary" />
          <div className="min-w-0 text-xs">
            <p className="font-semibold">
              {caps.isFetching ? "Checking Loupe availability…" : "Loupe execution unavailable"}
            </p>
            <p className="mt-1 leading-5 text-muted-foreground">
              Your scientific service must expose Loupe functions with R, Seurat, HDF5 and the
              official Louper converter. No files or results have been generated.
            </p>
            {caps.error && <p className="mt-2 break-all text-destructive">{caps.error.message}</p>}
          </div>
        </div>
      )}
      <div className="mb-4 flex flex-wrap gap-x-5 gap-y-2 border-b border-border pb-3 text-[11px] text-muted-foreground">
        {(["r", "loupeR", "hdf5", "louper"] as const).map((key) => (
          <span key={key}>
            {key === "r" ? "R" : key}:{" "}
            <strong className="text-foreground">{caps.data?.runtime[key] || "Unconfirmed"}</strong>
          </span>
        ))}
        <span>
          License setup:{" "}
          <strong className="text-foreground">
            {caps.data
              ? caps.data.runtime.license_ready
                ? "Confirmed by service"
                : "Required"
              : "Unconfirmed"}
          </strong>
        </span>
      </div>
      <div
        role="tablist"
        aria-label="Loupe views"
        className="mb-5 flex flex-wrap gap-1 border-b border-border"
      >
        {["Export", "Checks & utilities", "Outcomes", "Images"].map((item) => (
          <Button
            key={item}
            role="tab"
            aria-selected={tab === item}
            variant="ghost"
            size="sm"
            onClick={() => setTab(item)}
            className={
              tab === item
                ? "rounded-b-none border-b-2 border-primary text-primary"
                : "text-muted-foreground"
            }
          >
            {item}
          </Button>
        ))}
      </div>
      <div role="tabpanel" aria-label={tab}>
        {tab !== "Outcomes" && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void execute();
            }}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              {tab !== "Images" && (
                <label className="text-xs font-medium">
                  Function
                  <select
                    aria-label="Loupe function"
                    className={`${inputClass} mt-1`}
                    value={fn}
                    onChange={(e) =>
                      tab === "Export" ? setExportFn(e.target.value) : setUtilityFn(e.target.value)
                    }
                  >
                    {LOUPE_FUNCTIONS.filter((f) =>
                      tab === "Export" ? f.group === "Export" : f.group !== "Export",
                    ).map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.label} ({f.name})
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="text-xs font-medium">
                Output name
                <input
                  className={`${inputClass} mt-1`}
                  aria-label="Output name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  maxLength={106}
                />
              </label>
              <label className="text-xs font-medium">
                Cluster metadata columns
                <input
                  className={`${inputClass} mt-1`}
                  aria-label="Cluster metadata columns"
                  value={metadata}
                  onChange={(e) => setMetadata(e.target.value)}
                  placeholder="All eligible columns"
                />
              </label>
              <label className="text-xs font-medium">
                Projection names
                <input
                  className={`${inputClass} mt-1`}
                  aria-label="Projection names"
                  value={projections}
                  onChange={(e) => setProjections(e.target.value)}
                  placeholder="All eligible 2D projections"
                />
              </label>
              <label className="text-xs font-medium">
                Feature IDs source
                <select
                  className={`${inputClass} mt-1`}
                  aria-label="Feature IDs source"
                  value={
                    datasets.some((d) => d.dataset_id === featureDataset) ? featureDataset : ""
                  }
                  onChange={(e) => setFeatureDataset(e.target.value)}
                >
                  <option value="">Dataset feature IDs / library default</option>
                  {datasets.map((d) => (
                    <option key={d.dataset_id} value={d.dataset_id}>
                      {d.dataset_id}
                    </option>
                  ))}
                </select>
              </label>
              {tab === "Images" && (
                <>
                  <label className="text-xs font-medium">
                    Image format
                    <select
                      aria-label="Image format"
                      value={format}
                      className={`${inputClass} mt-1`}
                      onChange={(e) => setFormat(e.target.value)}
                    >
                      <option value="png">PNG</option>
                      <option value="svg">SVG</option>
                    </select>
                  </label>
                  <label className="text-xs font-medium">
                    Gene overlay
                    <input
                      aria-label="Gene overlay"
                      className={`${inputClass} mt-1`}
                      value={gene}
                      onChange={(e) => setGene(e.target.value)}
                    />
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="text-xs font-medium">
                      Width (px)
                      <input
                        type="number"
                        aria-label="Image width"
                        min={100}
                        max={8000}
                        required
                        value={width}
                        className={`${inputClass} mt-1`}
                        onChange={(e) => setWidth(Number(e.target.value))}
                      />
                    </label>
                    <label className="text-xs font-medium">
                      Height (px)
                      <input
                        type="number"
                        aria-label="Image height"
                        min={100}
                        max={8000}
                        required
                        value={height}
                        className={`${inputClass} mt-1`}
                        onChange={(e) => setHeight(Number(e.target.value))}
                      />
                    </label>
                  </div>
                </>
              )}
            </div>
            <label className="flex items-center gap-2 text-xs">
              <input type="checkbox" checked={dedup} onChange={(e) => setDedup(e.target.checked)} />
              Deduplicate equivalent cluster categories
            </label>
            <div className="border-t border-border pt-4">
              <Button size="sm" type="submit" disabled={Boolean(blocked || busy || inProgress)}>
                {busy || inProgress ? <LoaderCircle className="animate-spin" /> : <Play />}
                {tab === "Images"
                  ? "Generate image"
                  : tab === "Export"
                    ? "Generate export"
                    : "Run function"}
              </Button>
              {blocked && <p className="mt-2 text-xs text-muted-foreground">{blocked}</p>}
              {errorMessage && (
                <p role="alert" className="mt-2 break-words text-xs text-destructive">
                  {errorMessage}
                </p>
              )}
              {status.error && (
                <p role="alert" className="mt-2 break-words text-xs text-destructive">
                  {status.error.message}
                </p>
              )}
              {status.data && (
                <div className="mt-3 text-xs">
                  <p className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="size-4" />
                    {status.data.function} · {status.data.status}
                  </p>
                  {status.data.error && (
                    <p className="mt-1 text-destructive">{status.data.error}</p>
                  )}
                  <Button variant="link" size="sm" onClick={() => setTab("Outcomes")}>
                    View returned outcome
                  </Button>
                </div>
              )}
            </div>
          </form>
        )}
        {tab === "Checks & utilities" && (
          <p className="mt-4 text-xs leading-5 text-muted-foreground">
            Diagnostics may include sampled gene names and cell barcodes. Review returned reports
            before sharing. Runtime installation and license acceptance are service-administrator
            operations.
          </p>
        )}
        {tab === "Export" && (
          <p className="mt-4 border-t border-border pt-3 text-xs leading-5 text-muted-foreground">
            The supplied library exports gene-expression counts, cluster categories and 2D
            projections. Visium and Xenium expression are only partially supported; tissue images
            are not embedded by LoupeR.
          </p>
        )}
        {tab === "Images" && (
          <>
            <p className="mt-4 text-xs leading-5 text-muted-foreground">
              PNG/SVG rendering is a separate scientific-service operation, not a LoupeR function.
              No tissue-image export is provided by the uploaded library.
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {allRuns.flatMap((r) =>
                r.artifacts
                  .filter((a) => a.kind === "image")
                  .map((a) => (
                    <LoupeArtifact key={`${r.id}-${a.id}`} artifact={a} service={service} />
                  )),
              )}
            </div>
          </>
        )}
        {tab === "Outcomes" && (
          <>
            {runs.error && (
              <p role="alert" className="mb-3 text-xs text-destructive">
                {runs.error.message}
              </p>
            )}
            {allRuns.length === 0 ? (
              <EmptyState
                title="No Loupe outcomes returned"
                body={
                  runs.isFetching
                    ? "Loading observed runs…"
                    : "No conversion, validation report or image has been returned by the scientific service."
                }
                icon={<FileArchive className="size-6" />}
              />
            ) : (
              <div className="space-y-5">
                {allRuns.map((r) => (
                  <section key={r.id} className="border-b border-border pb-5">
                    <h2 className="break-words text-sm font-semibold">
                      {r.function}{" "}
                      <span className="font-normal text-muted-foreground">· {r.status}</span>
                    </h2>
                    <p className="mt-1 break-all font-mono text-[10px] text-muted-foreground">
                      {r.id}
                    </p>
                    {r.error && <p className="mt-2 text-xs text-destructive">{r.error}</p>}
                    {r.warnings.map((warning, i) => (
                      <p key={i} className="mt-2 text-xs text-muted-foreground">
                        {warning}
                      </p>
                    ))}
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      {r.artifacts.map((a) => (
                        <LoupeArtifact key={a.id} artifact={a} service={service} />
                      ))}
                    </div>
                    <details className="mt-3">
                      <summary className="cursor-pointer text-xs font-medium">
                        Returned output & provenance
                      </summary>
                      <pre className="scrollbar-thin mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-all rounded-md bg-panel-subtle p-3 text-[11px]">
                        {JSON.stringify(r.outputs, null, 2)}
                      </pre>
                    </details>
                  </section>
                ))}
              </div>
            )}
          </>
        )}
      </div>
      <div className="mt-6 flex items-center gap-2 border-t border-border py-3 text-[11px] text-muted-foreground">
        <ImageIcon className="size-4 shrink-0" />
        <span>
          Official R integration · 15 public library functions · Backend-confirmed availability only
        </span>
      </div>
    </Workspace>
  );
}
