import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { Image, Play } from "lucide-react";
import { useMemo, useState } from "react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { mbsi, type EmbeddingPoint, type EmbeddingRequest } from "@/lib/mbsi-api";

export const Route = createFileRoute("/imaging")({
  head: () => ({
    meta: [
      { title: "Multiplex imaging cohort maps — MBSI Studio" },
      {
        name: "description",
        content:
          "Compute PCA or t-SNE maps of multiplex image fields from observed feature vectors.",
      },
      { property: "og:title", content: "Multiplex imaging cohort maps — MBSI Studio" },
      {
        property: "og:description",
        content: "PCA and t-SNE image-cohort maps computed from observed feature vectors.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Imaging,
});

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--primary)",
];

function Scatter({
  points,
  onSelect,
  selected,
}: {
  points: EmbeddingPoint[];
  onSelect: (point: EmbeddingPoint) => void;
  selected?: string | undefined;
}) {
  const groups = useMemo(
    () => [...new Set(points.map((point) => point.sample_id ?? "—"))],
    [points],
  );
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const sx = (x: number) => 20 + ((x - x0) / (x1 - x0 || 1)) * 360;
  const sy = (y: number) => 280 - ((y - y0) / (y1 - y0 || 1)) * 260;

  return (
    <div>
      <svg
        viewBox="0 0 400 300"
        className="map-grid w-full rounded-xl border border-border bg-card"
        role="img"
        aria-label="Image embedding map"
      >
        {points.map((point) => (
          <circle
            key={point.image_id}
            cx={sx(point.x)}
            cy={sy(point.y)}
            r={point.image_id === selected ? 8 : 5}
            fill={COLORS[groups.indexOf(point.sample_id ?? "—") % COLORS.length]}
            stroke="var(--foreground)"
            strokeWidth={point.image_id === selected ? 1.5 : 0}
            tabIndex={0}
            className="cursor-pointer focus:outline-none"
            onClick={() => onSelect(point)}
            onKeyDown={(event) => event.key === "Enter" && onSelect(point)}
          >
            <title>{point.image_id}</title>
          </circle>
        ))}
      </svg>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground">
        {groups.map((group, index) => (
          <span key={group} className="flex items-center gap-1.5">
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: COLORS[index % COLORS.length] }}
            />
            {group}
          </span>
        ))}
      </div>
    </div>
  );
}

function Imaging() {
  const [text, setText] = useState("");
  const [method, setMethod] = useState<"pca" | "tsne">("pca");
  const [selected, setSelected] = useState<EmbeddingPoint>();
  const mutation = useMutation({ mutationFn: (body: EmbeddingRequest) => mbsi.embedding(body) });
  const [parseError, setParseError] = useState<string>();

  const run = () => {
    try {
      const body = JSON.parse(text) as EmbeddingRequest;
      setParseError(undefined);
      mutation.mutate({ ...body, method });
    } catch {
      setParseError("Input is not valid JSON.");
    }
  };

  return (
    <Workspace
      inspector={
        selected ? (
          <dl className="overflow-hidden rounded-xl border border-border text-xs">
            {Object.entries(selected).map(([key, value]) => (
              <div
                key={key}
                className="flex justify-between gap-3 border-b border-border px-3 py-2.5 last:border-b-0 odd:bg-panel-subtle/60"
              >
                <dt className="text-muted-foreground">{key}</dt>
                <dd className="break-all text-right font-mono">{String(value)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <EmptyState
            title="No field selected"
            body="Select a point on a backend-returned embedding to inspect its observed metadata."
          />
        )
      }
      dock={
        <div className="text-xs text-muted-foreground" role="status">
          <span className="mr-2 font-semibold text-foreground">Embedding status</span>
          {mutation.isPending
            ? "Computing embedding…"
            : mutation.isSuccess
              ? `Source: ${mutation.data.source} · Status: ${mutation.data.status} · ${mutation.data.coordinates.length} fields`
              : mutation.isError
                ? `Error: ${(mutation.error as Error).message}`
                : "Paste observed feature vectors and run. Raw TIFF/QPTIFF ingestion and thumbnails are not yet supported."}
        </div>
      }
    >
      <PageHeader
        title="Imaging cohort map"
        description="Explore image-level relationships using PCA or t-SNE computed by the scientific backend from observed feature vectors."
      />
      <div className="grid gap-4 2xl:grid-cols-[minmax(320px,0.8fr)_minmax(360px,1.2fr)]">
        <section className="rounded-xl border border-border bg-card p-4 shadow-panel">
          <label htmlFor="feat" className="text-sm font-semibold">
            Observed feature vectors
          </label>
          <p className="mb-3 mt-1 text-[11px] leading-4 text-muted-foreground">
            JSON with image_ids, features and optional metadata.
          </p>
          <Textarea
            id="feat"
            rows={13}
            className="resize-none bg-panel-subtle/40 font-mono text-xs"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder='{"image_ids": [...], "features": [[...]], "metadata": {...}}'
          />
          <div className="mt-3 flex items-center gap-2">
            <select
              aria-label="Embedding method"
              value={method}
              onChange={(event) => setMethod(event.target.value as "pca" | "tsne")}
              className="h-9 rounded-lg border border-input bg-background px-3 text-xs outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="pca">PCA</option>
              <option value="tsne">t-SNE</option>
            </select>
            <Button onClick={run} disabled={!text || mutation.isPending}>
              <Play />
              {mutation.isPending ? "Computing…" : "Compute map"}
            </Button>
          </div>
          {parseError && (
            <p className="mt-2 text-xs text-destructive" role="alert">
              {parseError}
            </p>
          )}
          <p className="mt-4 border-t border-border pt-3 text-[10px] leading-4 text-muted-foreground">
            Embedding concept inspired by MathOnco/Mistic (MIT, © 2021 IMO); independently
            implemented. Not for clinical inference.
          </p>
        </section>
        <section className="min-h-[390px] rounded-xl border border-border bg-card p-4 shadow-panel">
          <h2 className="mb-3 text-sm font-semibold">Cohort embedding</h2>
          {mutation.isSuccess && mutation.data.coordinates.length ? (
            <Scatter
              points={mutation.data.coordinates}
              onSelect={setSelected}
              selected={selected?.image_id}
            />
          ) : (
            <div className="h-[330px]">
              <EmptyState
                title="No embedding yet"
                body="Coordinates appear only after the backend returns observed results."
                icon={<Image className="h-6 w-6" strokeWidth={1.5} />}
              />
            </div>
          )}
        </section>
      </div>
    </Workspace>
  );
}
