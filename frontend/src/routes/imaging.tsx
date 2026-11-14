import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { mbsi, type EmbeddingPoint, type EmbeddingRequest } from "@/lib/mbsi-api";

export const Route = createFileRoute("/imaging")({
  head: () => ({
    meta: [
      { title: "Imaging — MBSI Studio" },
      { name: "description", content: "Compute PCA or t-SNE maps of multiplex image fields from observed feature vectors." },
      { property: "og:title", content: "Imaging — MBSI Studio" },
      { property: "og:description", content: "PCA / t-SNE image-cohort maps from observed feature vectors." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Imaging,
});

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)", "var(--primary)"];

function Scatter({ points, onSelect, selected }: { points: EmbeddingPoint[]; onSelect: (p: EmbeddingPoint) => void; selected?: string | undefined }) {
  const groups = useMemo(() => [...new Set(points.map((p) => p.sample_id ?? "—"))], [points]);
  const xs = points.map((p) => p.x), ys = points.map((p) => p.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const sx = (x: number) => 20 + ((x - x0) / (x1 - x0 || 1)) * 360;
  const sy = (y: number) => 280 - ((y - y0) / (y1 - y0 || 1)) * 260;
  return (
    <div>
      <svg viewBox="0 0 400 300" className="w-full rounded-lg border border-border bg-card" role="img" aria-label="Image embedding map">
        {points.map((p) => (
          <circle
            key={p.image_id}
            cx={sx(p.x)} cy={sy(p.y)} r={p.image_id === selected ? 8 : 5}
            fill={COLORS[groups.indexOf(p.sample_id ?? "—") % COLORS.length]}
            stroke="var(--foreground)" strokeWidth={p.image_id === selected ? 1.5 : 0}
            tabIndex={0} className="cursor-pointer focus:outline-none"
            onClick={() => onSelect(p)} onKeyDown={(e) => e.key === "Enter" && onSelect(p)}
          ><title>{p.image_id}</title></circle>
        ))}
      </svg>
      <div className="mt-2 flex flex-wrap gap-3 text-xs">
        {groups.map((g, i) => (
          <span key={g} className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />{g}
          </span>
        ))}
      </div>
    </div>
  );
}

function Imaging() {
  const [text, setText] = useState("");
  const [method, setMethod] = useState<"pca" | "tsne">("pca");
  const [sel, setSel] = useState<EmbeddingPoint>();
  const m = useMutation({ mutationFn: (b: EmbeddingRequest) => mbsi.embedding(b) });
  const [parseErr, setParseErr] = useState<string>();

  const run = () => {
    try {
      const body = JSON.parse(text) as EmbeddingRequest;
      setParseErr(undefined);
      m.mutate({ ...body, method });
    } catch {
      setParseErr("Input is not valid JSON.");
    }
  };

  return (
    <Workspace
      inspector={
        sel ? (
          <dl className="space-y-1 text-sm">
            {Object.entries(sel).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2"><dt className="text-muted-foreground">{k}</dt><dd className="font-mono text-xs">{String(v)}</dd></div>
            ))}
          </dl>
        ) : undefined
      }
      dock={
        <p className="text-sm text-muted-foreground">
          {m.isPending ? "Computing embedding…" : m.isSuccess ? `Source: ${m.data.source} · status: ${m.data.status} · ${m.data.coordinates.length} fields` : m.isError ? `Error: ${(m.error as Error).message}` : "Paste observed feature vectors and run. Raw TIFF/QPTIFF ingestion and thumbnails are not yet supported."}
        </p>
      }
    >
      <h1 className="mb-1 text-xl font-semibold">Imaging cohort map</h1>
      <p className="mb-4 text-xs text-muted-foreground">Embedding concept inspired by MathOnco/Mistic (MIT, © 2021 IMO); independently implemented. Not for clinical inference.</p>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-2">
          <label htmlFor="feat" className="text-sm font-medium">Feature vectors (JSON: image_ids, features, metadata)</label>
          <Textarea id="feat" rows={12} className="font-mono text-xs" value={text} onChange={(e) => setText(e.target.value)} placeholder='{"image_ids": [...], "features": [[...]], "metadata": {...}}' />
          <div className="flex items-center gap-2">
            <select aria-label="Method" value={method} onChange={(e) => setMethod(e.target.value as "pca" | "tsne")} className="rounded-md border border-input bg-background px-2 py-1.5 text-sm">
              <option value="pca">PCA</option><option value="tsne">t-SNE</option>
            </select>
            <Button onClick={run} disabled={!text || m.isPending}>Compute map</Button>
          </div>
          {parseErr && <p className="text-sm text-destructive">{parseErr}</p>}
        </div>
        <div className="min-h-64">
          {m.isSuccess && m.data.coordinates.length ? (
            <Scatter points={m.data.coordinates} onSelect={setSel} selected={sel?.image_id} />
          ) : (
            <EmptyState title="No embedding yet" body="Coordinates appear only after the backend returns observed results." />
          )}
        </div>
      </div>
    </Workspace>
  );
}
