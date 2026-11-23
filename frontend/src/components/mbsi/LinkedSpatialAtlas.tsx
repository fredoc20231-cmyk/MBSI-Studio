import { useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import {
  mbsi,
  type DatasetSummary,
  type SpatialResponse,
  type SpatialSelectionResponse,
} from "@/lib/mbsi-api";

type Point = [number, number];
const PALETTE = ["#38a3a5", "#d89a36", "#b25b7d", "#4f8d42", "#764fa5", "#d04b42", "#22577a"];
const MAX_PANELS = 4;

function extent(data: SpatialResponse) {
  const xs = data.points.map((p) => p.x);
  const ys = data.points.map((p) => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = Math.max(1, maxX - minX), spanY = Math.max(1, maxY - minY);
  const pad = Math.max(spanX, spanY) * 0.06;
  return {
    view: [minX - pad, minY - pad, spanX + 2 * pad, spanY + 2 * pad],
    radius: Math.max(spanX, spanY) / 175,
  };
}

function downloadBarcodes(datasetId: string, result: SpatialSelectionResponse) {
  const quote = (v: string) => '"' + v.replaceAll('"', '""') + '"';
  const rows = ["dataset_id,barcode", ...result.barcodes.map((id) => quote(datasetId) + "," + quote(id))];
  const url = URL.createObjectURL(new Blob([rows.join("\n") + "\n"], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "mbsi-region-" + datasetId + ".csv";
  link.click();
  URL.revokeObjectURL(url);
}

function formatValue(value: number | null | undefined) {
  return value == null ? "—" : value.toPrecision(4);
}

/**
 * Linked sample-level color and selection controls inspired by spatialscape.
 * Each panel stays in its own native coordinate system: no false registration.
 * Selection summaries come from the complete observed dataset via the backend.
 */
export function LinkedSpatialAtlas({
  selectedIds,
  datasets,
}: {
  selectedIds: readonly string[];
  datasets: readonly DatasetSummary[];
}) {
  const ids = selectedIds.slice(0, MAX_PANELS);
  const configuredViewer = (import.meta.env["VITE_MBSI_SPATIALSCAPE_URL"] as string | undefined)?.trim() || "";
  const viewerUrl = configuredViewer.startsWith("https://") ||
    (import.meta.env.DEV && (
      configuredViewer.startsWith("http://localhost:") ||
      configuredViewer.startsWith("http://127.0.0.1:")
    )) ? configuredViewer : "";
  const [mode, setMode] = useState<"gene" | "annotation">("gene");
  const [featureInput, setFeatureInput] = useState("");
  const [thresholdInput, setThresholdInput] = useState("");
  const [drawing, setDrawing] = useState("");
  const [polygons, setPolygons] = useState<Record<string, Point[]>>({});
  const [summaries, setSummaries] = useState<Record<string, SpatialSelectionResponse>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");

  const features = useQuery({
    queryKey: ["linked-atlas-features", ids[0]],
    queryFn: () => mbsi.features(ids[0]),
    enabled: ids.length > 0,
    retry: false,
  });
  const fallback = mode === "gene" ? features.data?.genes[0] : features.data?.annotations[0];
  const feature = featureInput.trim() || fallback || "";
  const numericThreshold = thresholdInput.trim() === "" ? null : Number(thresholdInput);
  const thresholdValid = numericThreshold === null || Number.isFinite(numericThreshold);

  const queries = useQueries({
    queries: ids.map((id) => ({
      queryKey: ["linked-atlas-spatial", id, mode, feature],
      queryFn: () => mbsi.spatial(
        id,
        mode === "gene" ? { gene: feature, limit: 5000 } : { annotation: feature, limit: 5000 },
      ),
      enabled: Boolean(feature),
      retry: false,
      staleTime: 60_000,
    })),
  });

  const data = queries.map((q) => q.data);
  const numericRange = useMemo(() => {
    const numbers = data.flatMap((item) => item && !item.categorical
      ? item.points.map((p) => Number(p.value)).filter(Number.isFinite)
      : []);
    return numbers.length ? [Math.min(...numbers), Math.max(...numbers)] as const : [0, 1] as const;
  }, [data]);
  const categories = useMemo(
    () => Array.from(new Set(data.flatMap((item) => item && item.categorical
      ? item.points.map((p) => String(p.value)) : []))).sort(),
    [data],
  );

  const color = (value: string | number) => {
    if (mode === "annotation") {
      const index = categories.indexOf(String(value));
      return PALETTE[(Math.max(0, index)) % PALETTE.length];
    }
    const t = (Number(value) - numericRange[0]) / (numericRange[1] - numericRange[0] || 1);
    return "hsl(" + Math.round(220 - 220 * Math.max(0, Math.min(1, t))) + " 75% 45%)";
  };

  function resetFeature(nextMode: "gene" | "annotation") {
    setMode(nextMode);
    setFeatureInput("");
    setThresholdInput("");
    setPolygons({});
    setSummaries({});
    setErrors({});
  }

  async function analyzeRegion(id: string) {
    const polygon = polygons[id] || [];
    if (polygon.length < 3 || !feature || !thresholdValid) return;
    setBusy(id);
    setErrors((old) => ({ ...old, [id]: "" }));
    try {
      const summary = await mbsi.selectRegion(id, {
        polygon,
        ...(mode === "gene" ? { gene: feature } : { annotation: feature }),
        ...(mode === "gene" && numericThreshold !== null ? { threshold: numericThreshold } : {}),
      });
      setSummaries((old) => ({ ...old, [id]: summary }));
    } catch (error) {
      setErrors((old) => ({ ...old, [id]: error instanceof Error ? error.message : String(error) }));
    } finally {
      setBusy("");
    }
  }

  return (
    <section aria-label="Linked spatial atlas" className="mt-3 rounded-xl border border-border bg-card p-4 shadow-panel">
      <h2 className="text-sm font-semibold">Linked tissue atlas and exact region analysis</h2>
      {viewerUrl && (
        <a href={viewerUrl} target="_blank" rel="noopener noreferrer"
          className="mt-2 inline-flex rounded-md border border-border px-3 py-1.5 text-xs text-primary">
          Open separately hosted high-resolution SpatialScape atlas
        </a>
      )}
      <p className="mt-1 text-xs leading-5 text-muted-foreground">
        Synchronized feature and color scales across up to four observed samples. Draw a polygon
        to obtain exact full-dataset region summaries; plots alone may be downsampled.
        Tissue panels retain source coordinates and are not automatically registered.
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="flex min-w-32 flex-col gap-1 text-xs">
          Display
          <select aria-label="Atlas value type" value={mode}
            onChange={(e) => resetFeature(e.target.value as "gene" | "annotation")}
            className="h-9 rounded-md border border-input bg-background px-2">
            <option value="gene">Observed expression</option>
            <option value="annotation">Observed annotation</option>
          </select>
        </label>
        <label className="flex min-w-48 flex-1 flex-col gap-1 text-xs">
          {mode === "gene" ? "Gene (exact ID)" : "Annotation (exact column)"}
          <input aria-label="Atlas feature" value={featureInput} placeholder={fallback || "Enter feature"}
            onChange={(e) => {
              setFeatureInput(e.target.value); setSummaries({}); setErrors({});
            }}
            className="h-9 rounded-md border border-input bg-background px-3" />
        </label>
        {mode === "gene" && (
          <label className="flex w-36 flex-col gap-1 text-xs">
            Minimum expression
            <input aria-label="Atlas expression threshold" type="number" value={thresholdInput}
              onChange={(e) => { setThresholdInput(e.target.value); setSummaries({}); }}
              className="h-9 rounded-md border border-input bg-background px-2" />
          </label>
        )}
      </div>
      {mode === "gene" && thresholdInput !== "" && !thresholdValid && (
        <p role="alert" className="mt-2 text-xs text-destructive">Enter a finite threshold.</p>
      )}
      {selectedIds.length > MAX_PANELS && (
        <p className="mt-2 text-xs text-amber-700">
          Only the first {MAX_PANELS} selected samples are displayed. Other samples remain selected for the workflow comparison.
        </p>
      )}
      {ids.length === 0 ? (
        <p className="mt-4 rounded-lg border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
          Select samples above to open linked observed tissue maps.
        </p>
      ) : (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {ids.map((id, index) => {
            const sample = datasets.find((d) => d.dataset_id === id);
            const response = data[index];
            const query = queries[index];
            const polygon = polygons[id] || [];
            const summary = summaries[id];
            const geometry = response && response.points.length > 0 ? extent(response) : null;
            const points = response?.points.filter((p) =>
              mode !== "gene" || numericThreshold === null || Number(p.value) >= numericThreshold) || [];
            return (
              <article key={id} className="min-w-0 overflow-hidden rounded-lg border border-border bg-background">
                <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2">
                  <div>
                    <h3 className="text-xs font-semibold">{sample?.sample_id || id}</h3>
                    <p className="text-[10px] text-muted-foreground">{sample?.platform || "Observed"} · {id}</p>
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {response ? response.returned_observations + "/" + response.total_observations : "Awaiting data"}
                  </span>
                </div>
                <div className="p-3">
                  {!feature ? (
                    <p className="py-16 text-center text-xs text-muted-foreground">Enter a gene or annotation to view observed tissue.</p>
                  ) : query.isPending ? (
                    <p className="py-20 text-center text-xs text-muted-foreground">Loading observed tissue…</p>
                  ) : query.isError ? (
                    <p role="alert" className="py-16 text-center text-xs text-destructive">
                      {query.error instanceof Error ? query.error.message : "Feature unavailable in this sample"}
                    </p>
                  ) : response && geometry ? (
                    <div>
                      <svg role="img" aria-label={"Spatial atlas for " + id}
                        viewBox={geometry.view.join(" ")}
                        preserveAspectRatio="xMidYMid meet"
                        className={"h-64 w-full rounded-md border border-border bg-card " +
                          (drawing === id ? "cursor-crosshair" : "")}
                        onClick={(event) => {
                          if (drawing !== id) return;
                          const matrix = event.currentTarget.getScreenCTM();
                          if (!matrix) return;
                          const pointer = event.currentTarget.createSVGPoint();
                          pointer.x = event.clientX;
                          pointer.y = event.clientY;
                          const local = pointer.matrixTransform(matrix.inverse());
                          if (!Number.isFinite(local.x) || !Number.isFinite(local.y)) return;
                          setPolygons((old) => ({
                            ...old,
                            [id]: [...(old[id] || []), [local.x, local.y]],
                          }));
                          setSummaries((old) => { const next = { ...old }; delete next[id]; return next; });
                        }}>
                        {points.map((point) => (
                          <circle key={point.barcode} cx={point.x} cy={point.y} r={geometry.radius}
                            fill={color(point.value)} fillOpacity="0.85">
                            <title>{point.barcode + ": " + point.value}</title>
                          </circle>
                        ))}
                        {polygon.length > 1 && (
                          <polyline points={polygon.map((p) => p.join(",")).join(" ")}
                            fill="none" stroke="#e9a83f" strokeWidth={geometry.radius * 1.4}
                            strokeDasharray={geometry.radius * 2 + " " + geometry.radius} />
                        )}
                        {polygon.map((point, i) => (
                          <circle key={i} cx={point[0]} cy={point[1]} r={geometry.radius * 2.3}
                            fill="#e9a83f" />
                        ))}
                      </svg>
                      <p className="mt-2 text-[10px] text-muted-foreground">
                        {response.downsampled ? "Downsampled visual sample" : "All observed points"}
                        {" · " + points.length + " visible after display filter"}
                        {" · " + response.coordinate_system + " · " + response.source_layer}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <button type="button" aria-pressed={drawing === id}
                          onClick={() => setDrawing((old) => old === id ? "" : id)}
                          className="rounded-md border border-border px-3 py-1.5 text-[11px]">
                          {drawing === id ? "Finish polygon" : "Draw ROI"}
                        </button>
                        <button type="button" disabled={polygon.length < 3 || busy !== "" || !thresholdValid}
                          onClick={() => void analyzeRegion(id)}
                          className="rounded-md bg-primary px-3 py-1.5 text-[11px] text-primary-foreground disabled:opacity-50">
                          {busy === id ? "Analyzing…" : "Analyze exact ROI"}
                        </button>
                        <button type="button" onClick={() => {
                          setPolygons((old) => ({ ...old, [id]: [] }));
                          setSummaries((old) => { const next = { ...old }; delete next[id]; return next; });
                        }} className="rounded-md border border-border px-3 py-1.5 text-[11px]">
                          Clear
                        </button>
                      </div>
                      {polygon.length > 0 && <p className="mt-1 text-[10px] text-muted-foreground">
                        {polygon.length} polygon vertices. Click Draw ROI again to stop adding points.
                      </p>}
                    </div>
                  ) : (
                    <p className="py-16 text-center text-xs text-muted-foreground">
                      {feature ? "No observed points for this feature" : "Enter an observed feature to start"}
                    </p>
                  )}
                  {errors[id] && <p role="alert" className="mt-3 text-xs text-destructive">{errors[id]}</p>}
                  {summary && (
                    <div className="mt-3 rounded-lg border border-border bg-card p-3 text-[11px]">
                      <p className="font-semibold">
                        Exact selected cells/spots: {summary.selected_observations.toLocaleString()}
                      </p>
                      {summary.categorical ? (
                        <p className="mt-1 text-muted-foreground">
                          {Object.entries(summary.statistics.category_counts || {}).map(([k, v]) =>
                            k + ": " + v).join(" · ") || "No observations"}
                        </p>
                      ) : (
                        <p className="mt-1 text-muted-foreground">
                          Mean: {formatValue(summary.statistics.mean)}
                          {" · Median: " + formatValue(summary.statistics.median)}
                          {" · Detected: " + (summary.statistics.fraction_detected == null
                            ? "—" : (summary.statistics.fraction_detected * 100).toFixed(1) + "%")}
                          {summary.statistics.above_threshold != null &&
                            " · Above threshold: " + summary.statistics.above_threshold}
                        </p>
                      )}
                      <button type="button" onClick={() => downloadBarcodes(id, summary)}
                        disabled={summary.barcodes.length === 0}
                        className="mt-2 rounded-md border border-border px-3 py-1.5 disabled:opacity-50">
                        Export selected IDs (CSV)
                      </button>
                      {summary.barcodes_truncated && <p className="mt-1 text-amber-700">
                        CSV capped at 5,000 identifiers; total selected count is exact.
                      </p>}
                      <p className="mt-1 text-muted-foreground">
                        Descriptive statistics only; no condition-level differential expression.
                      </p>
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
      {ids.length > 0 && mode === "annotation" && categories.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
          {categories.slice(0, 12).map((category) => (
            <span key={category} className="inline-flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color(category) }} />
              {category}
            </span>
          ))}
          {categories.length > 12 && <span>+ {categories.length - 12} additional categories</span>}
        </div>
      )}
      {ids.length > 0 && feature && mode === "gene" && (
        <p className="mt-3 text-[11px] text-muted-foreground">
          Shared displayed range across loaded panels: {formatValue(numericRange[0])}
          {" – " + formatValue(numericRange[1])}. Compare biological conditions only after normalization
          and biological-replicate-aware statistical testing.
        </p>
      )}
    </section>
  );
}
