import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertCircle,
  BarChart3,
  Check,
  Columns2,
  GitCompare,
  Layers3,
  LoaderCircle,
  LockKeyhole,
  Network,
  Play,
  Route as Trajectory,
  Rows2,
  ScatterChart,
  Sigma,
  UsersRound,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";
import {
  alignScalarMetrics,
  buildComparisonRequests,
  COMPARISON_LEVELS,
  getObservedDetails,
  type ComparisonLevel,
} from "@/lib/comparison";
import { mbsi, type DatasetUploadResponse, type WorkflowRunResponse } from "@/lib/mbsi-api";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare spatial samples — MBSI Studio" },
      {
        name: "description",
        content:
          "Run multi-sample comparisons of gene expression, clusters, spatial domains, phenotypes and spatial statistics with observed backend results.",
      },
      { property: "og:title", content: "Compare spatial samples — MBSI Studio" },
      {
        property: "og:description",
        content:
          "Aligned, traceable comparisons across uploaded spatial omics samples and analysis levels.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Compare,
});

const LEVEL_ICONS: Record<string, LucideIcon> = {
  expression: BarChart3,
  clusters: ScatterChart,
  domains: Layers3,
  phenotypes: UsersRound,
  "spatial-stats": Sigma,
  niches: Network,
  interactions: GitCompare,
  trajectories: Trajectory,
};

function runKey(levelId: string, datasetId: string) {
  return `${levelId}:${datasetId}`;
}

function metricLabel(key: string) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function SampleResult({
  datasetId,
  dataset,
  level,
  run,
  error,
}: {
  datasetId: string;
  dataset: DatasetUploadResponse | undefined;
  level: ComparisonLevel;
  run: WorkflowRunResponse | undefined;
  error: string | undefined;
}) {
  const details = run ? getObservedDetails(run.outputs, level.detailPaths) : {};
  const failed = run?.status === "failed" || run?.status === "stub";

  return (
    <article className="flex min-h-56 min-w-0 flex-col rounded-xl border border-border bg-card shadow-panel">
      <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-semibold" title={datasetId}>
            {datasetId}
          </h3>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {dataset?.platform || "Uploaded dataset"}
          </p>
        </div>
        {run && (
          <span
            className={`shrink-0 rounded-full px-2 py-1 text-[10px] font-medium ${failed ? "bg-destructive/10 text-destructive" : "bg-success/10 text-success"}`}
          >
            {run.status}
          </span>
        )}
      </header>
      <div className="flex flex-1 flex-col gap-3 p-4">
        {error && (
          <div
            role="alert"
            className="flex gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span className="break-words">{error}</span>
          </div>
        )}
        {!error && !run && (
          <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-border p-5 text-center text-xs text-muted-foreground">
            Run this comparison to request observed outputs for the sample.
          </div>
        )}
        {run?.warnings.map((warning, index) => (
          <div
            key={`${warning}-${index}`}
            className="rounded-lg bg-warning/10 p-3 text-[11px] leading-4 text-foreground"
          >
            {warning}
          </div>
        ))}
        {run && Object.keys(details).length > 0 && (
          <div className="space-y-2">
            {Object.entries(details).map(([name, value]) => (
              <details key={name} className="rounded-lg border border-border bg-panel-subtle/50">
                <summary className="cursor-pointer px-3 py-2 text-xs font-medium">
                  {name.split(".").at(-1)?.replaceAll("_", " ")}
                </summary>
                <pre className="scrollbar-thin max-h-80 overflow-auto whitespace-pre-wrap border-t border-border p-3 font-mono text-[10px] leading-4">
                  {JSON.stringify(value, null, 2)}
                </pre>
              </details>
            ))}
          </div>
        )}
        {run && Object.keys(details).length === 0 && !failed && (
          <p className="text-xs text-muted-foreground">
            The workflow completed without level-specific detailed outputs.
          </p>
        )}
        {run && (
          <p className="mt-auto pt-1 font-mono text-[10px] text-muted-foreground">
            Run ID: {run.run_id}
          </p>
        )}
      </div>
    </article>
  );
}

function Compare() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [activeId, setActiveId] = useState("expression");
  const [layout, setLayout] = useState("Columns");
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<Record<string, WorkflowRunResponse>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const datasetsQuery = useQuery<DatasetUploadResponse[]>({
    queryKey: ["uploaded-datasets"],
    queryFn: () => [],
    initialData: [],
    enabled: false,
  });
  const datasets = datasetsQuery.data;
  const activeLevel: ComparisonLevel =
    COMPARISON_LEVELS.find((level) => level.id === activeId) ?? COMPARISON_LEVELS[0];
  const currentRuns = selectedIds.flatMap((datasetId) => {
    const run = runs[runKey(activeLevel.id, datasetId)];
    return run ? [{ datasetId, run }] : [];
  });
  const completedRuns = currentRuns.filter(
    ({ run }) => run.status !== "failed" && run.status !== "stub",
  );
  const metricRows = alignScalarMetrics(
    completedRuns.map(({ datasetId, run }) => ({ datasetId, outputs: run.outputs })),
  );

  function toggleDataset(datasetId: string) {
    setSelectedIds((current) =>
      current.includes(datasetId)
        ? current.filter((id) => id !== datasetId)
        : [...current, datasetId],
    );
  }

  async function runComparison() {
    const requests = buildComparisonRequests(activeLevel, selectedIds);
    if (requests.length === 0) return;

    setRunning(true);
    const settled = await Promise.allSettled(requests.map((request) => mbsi.runWorkflow(request)));
    setRuns((current) => {
      const next = { ...current };
      settled.forEach((result, index) => {
        const key = runKey(activeLevel.id, requests[index]!.dataset_id);
        if (result.status === "fulfilled") next[key] = result.value;
        else delete next[key];
      });
      return next;
    });
    setErrors((current) => {
      const next = { ...current };
      settled.forEach((result, index) => {
        const key = runKey(activeLevel.id, requests[index]!.dataset_id);
        if (result.status === "rejected") next[key] = (result.reason as Error).message;
        else delete next[key];
      });
      return next;
    });
    setRunning(false);

    const failed = settled.filter(
      (result) =>
        result.status === "rejected" ||
        (result.status === "fulfilled" && ["failed", "stub"].includes(result.value.status)),
    ).length;
    if (failed > 0) {
      toast.error(`${failed} sample workflow${failed === 1 ? "" : "s"} did not complete`, {
        description: "Review the returned status, warnings and request errors in each sample card.",
      });
    } else {
      toast.success("Comparison completed", {
        description: `Observed ${activeLevel.label.toLowerCase()} outputs returned for ${selectedIds.length} samples.`,
      });
    }
  }

  return (
    <Workspace>
      <PageHeader
        title="Compare samples"
        description="Select two or more uploaded samples, choose a biological level and align observed results from independent backend workflows."
        action={
          <UploadButton
            label="Add sample"
            onUploaded={(dataset) =>
              setSelectedIds((current) =>
                current.includes(dataset.dataset_id) ? current : [...current, dataset.dataset_id],
              )
            }
          />
        }
      />

      <section
        aria-labelledby="sample-selection-title"
        className="rounded-xl border border-border bg-card p-4 shadow-panel"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="sample-selection-title" className="text-sm font-semibold">
              1. Select samples
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {selectedIds.length} selected · datasets uploaded in this session
            </p>
          </div>
          {datasets.length > 1 && (
            <button
              type="button"
              onClick={() => setSelectedIds(datasets.map((dataset) => dataset.dataset_id))}
              className="text-xs font-medium text-primary hover:underline"
            >
              Select all
            </button>
          )}
        </div>
        {datasets.length === 0 ? (
          <div className="mt-4 h-44">
            <EmptyState
              title="No uploaded samples in this session"
              body="Add at least two observed datasets. Their returned dataset identifiers will become available for comparison here."
              icon={<GitCompare className="h-6 w-6" strokeWidth={1.5} />}
            />
          </div>
        ) : (
          <div className="mt-4 grid gap-2 sm:grid-cols-2 2xl:grid-cols-3">
            {datasets.map((dataset) => {
              const selected = selectedIds.includes(dataset.dataset_id);
              return (
                <label
                  key={dataset.dataset_id}
                  className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${selected ? "border-primary bg-accent" : "border-border hover:bg-muted"}`}
                >
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggleDataset(dataset.dataset_id)}
                    className="sr-only"
                  />
                  <span
                    aria-hidden
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${selected ? "border-primary bg-primary text-primary-foreground" : "border-input bg-background"}`}
                  >
                    {selected && <Check className="h-3.5 w-3.5" />}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-xs font-medium" title={dataset.dataset_id}>
                      {dataset.dataset_id}
                    </span>
                    <span className="mt-0.5 block text-[11px] text-muted-foreground">
                      {dataset.platform}
                    </span>
                  </span>
                </label>
              );
            })}
          </div>
        )}
      </section>

      <section
        aria-labelledby="comparison-level-title"
        className="mt-3 overflow-hidden rounded-xl border border-border bg-card shadow-panel"
      >
        <div className="border-b border-border px-4 py-3">
          <h2 id="comparison-level-title" className="text-sm font-semibold">
            2. Choose comparison level
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">{activeLevel.description}</p>
        </div>
        <div
          className="scrollbar-thin flex overflow-x-auto border-b border-border px-2"
          role="tablist"
          aria-label="Comparison levels"
        >
          {COMPARISON_LEVELS.map((level: ComparisonLevel) => {
            const Icon = LEVEL_ICONS[level.id] ?? GitCompare;
            return (
              <button
                key={level.id}
                type="button"
                role="tab"
                aria-selected={activeLevel.id === level.id}
                onClick={() => setActiveId(level.id)}
                className={`relative flex h-12 shrink-0 items-center gap-1.5 px-3 text-xs font-medium ${activeLevel.id === level.id ? "text-primary after:absolute after:inset-x-2 after:bottom-0 after:h-0.5 after:bg-primary" : "text-muted-foreground hover:text-foreground"}`}
              >
                {level.module ? (
                  <Icon className="h-3.5 w-3.5" />
                ) : (
                  <LockKeyhole className="h-3.5 w-3.5" />
                )}
                {level.label}
              </button>
            );
          })}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div className="text-xs text-muted-foreground">
            {activeLevel.module
              ? selectedIds.length < 2
                ? "Select at least two samples to run this comparison."
                : `One ${activeLevel.module} workflow will run per selected sample; demo data is disabled.`
              : activeLevel.unavailableReason}
          </div>
          <button
            type="button"
            disabled={!activeLevel.module || selectedIds.length < 2 || running}
            onClick={runComparison}
            className="inline-flex h-9 items-center gap-2 rounded-lg bg-primary px-4 text-xs font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {running ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : activeLevel.module ? (
              <Play className="h-4 w-4" />
            ) : (
              <LockKeyhole className="h-4 w-4" />
            )}
            {running ? "Running sample workflows…" : `Compare ${selectedIds.length} samples`}
          </button>
        </div>
      </section>

      <section
        aria-labelledby="comparison-results-title"
        className="mt-3 rounded-xl border border-border bg-card p-4 shadow-panel"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="comparison-results-title" className="text-sm font-semibold">
              3. Observed comparison results
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Missing values remain blank; no cross-sample statistics are calculated in the browser.
            </p>
          </div>
          <div className="flex gap-1" aria-label="Result layout">
            <button
              type="button"
              aria-label="Column comparison"
              aria-pressed={layout === "Columns"}
              onClick={() => setLayout("Columns")}
              className={`rounded-md p-2 ${layout === "Columns" ? "bg-accent text-primary" : "text-muted-foreground"}`}
            >
              <Columns2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="Row comparison"
              aria-pressed={layout === "Rows"}
              onClick={() => setLayout("Rows")}
              className={`rounded-md p-2 ${layout === "Rows" ? "bg-accent text-primary" : "text-muted-foreground"}`}
            >
              <Rows2 className="h-4 w-4" />
            </button>
          </div>
        </div>

        {!activeLevel.module ? (
          <div className="mt-4 h-56">
            <EmptyState
              title={`${activeLevel.label} comparison is not exposed by the API`}
              body={activeLevel.unavailableReason ?? "This scientific workflow is unavailable."}
              icon={<LockKeyhole className="h-6 w-6" strokeWidth={1.5} />}
            />
          </div>
        ) : currentRuns.length === 0 &&
          !selectedIds.some((datasetId) => errors[runKey(activeLevel.id, datasetId)]) ? (
          <div className="mt-4 h-56">
            <EmptyState
              title="No comparison run yet"
              body="Select at least two samples and run the configured workflows. Returned summaries and detailed outputs will appear here with their run identifiers."
              icon={<GitCompare className="h-6 w-6" strokeWidth={1.5} />}
            />
          </div>
        ) : (
          <>
            {metricRows.length > 0 && (
              <div className="scrollbar-thin mt-4 overflow-x-auto rounded-lg border border-border">
                <table className="w-full min-w-[560px] border-collapse text-left text-xs">
                  <thead className="bg-panel-subtle text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">Observed metric</th>
                      {completedRuns.map(({ datasetId }) => (
                        <th
                          key={datasetId}
                          className="max-w-48 truncate px-3 py-2 font-medium"
                          title={datasetId}
                        >
                          {datasetId}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {metricRows.map((row) => (
                      <tr key={row.key} className="border-t border-border">
                        <th className="px-3 py-2 font-medium">{metricLabel(row.key)}</th>
                        {completedRuns.map(({ datasetId }) => (
                          <td key={datasetId} className="px-3 py-2 font-mono">
                            {row.values[datasetId] ?? "—"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div
              className={`mt-4 grid gap-3 ${layout === "Columns" ? "md:grid-cols-2 2xl:grid-cols-3" : "grid-cols-1"}`}
            >
              {selectedIds.map((datasetId) => (
                <SampleResult
                  key={datasetId}
                  datasetId={datasetId}
                  dataset={datasets.find((dataset) => dataset.dataset_id === datasetId)}
                  level={activeLevel}
                  run={runs[runKey(activeLevel.id, datasetId)]}
                  error={errors[runKey(activeLevel.id, datasetId)]}
                />
              ))}
            </div>
          </>
        )}
      </section>
    </Workspace>
  );
}
