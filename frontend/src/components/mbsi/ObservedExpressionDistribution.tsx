import { useMemo } from "react";
import type { SpatialResponse } from "@/lib/mbsi-api";

/**
 * Descriptive distribution adapted from the legacy iVisio expression/matrix UI.
 * Operates ONLY on returned observed values; never infers p-values or sample-level DE.
 */
export function ObservedExpressionDistribution({ data }: { data: SpatialResponse }) {
  const distribution = useMemo(() => {
    if (data.categorical) return null;
    const values = data.points.map((p) => Number(p.value)).filter(Number.isFinite);
    if (!values.length) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = Array.from({ length: 20 }, () => 0);
    for (const value of values) {
      const index = max === min ? 0 : Math.min(19, Math.floor(((value - min) / (max - min)) * 20));
      bins[index] += 1;
    }
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted.length % 2
      ? sorted[(sorted.length - 1) / 2]
      : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2;
    return { bins, min, max, median, count: values.length, maxBin: Math.max(...bins, 1) };
  }, [data]);
  if (!distribution) {
    return <p className="text-xs text-muted-foreground">Select a numeric gene expression layer to inspect its distribution.</p>;
  }
  return (
    <section aria-label="Observed expression distribution" className="rounded-lg border border-border p-3">
      <h3 className="text-xs font-semibold">Expression distribution · {data.feature}</h3>
      <p className="mt-1 text-[11px] text-muted-foreground">Observed values in the current spatial response ({data.source_layer})</p>
      <svg viewBox="0 0 420 130" role="img" aria-label={"Histogram of " + distribution.count + " observed values"} className="mt-2 w-full">
        <line x1="14" y1="110" x2="408" y2="110" stroke="currentColor" opacity=".3" />
        {distribution.bins.map((count, index) => (
          <rect key={index} x={17 + index * 19.3} y={110 - (count / distribution.maxBin) * 94}
            width="17" height={(count / distribution.maxBin) * 94} rx="1.5" fill="#38A3A5">
            <title>{`Bin ${index + 1}: ${count} observations`}</title>
          </rect>
        ))}
      </svg>
      <dl className="mt-1 grid grid-cols-3 gap-2 text-[11px]">
        <div><dt className="text-muted-foreground">Min</dt><dd className="font-mono">{distribution.min.toPrecision(4)}</dd></div>
        <div><dt className="text-muted-foreground">Median</dt><dd className="font-mono">{distribution.median.toPrecision(4)}</dd></div>
        <div><dt className="text-muted-foreground">Max</dt><dd className="font-mono">{distribution.max.toPrecision(4)}</dd></div>
      </dl>
      <p className="mt-2 text-[10px] leading-4 text-muted-foreground">
        {data.downsampled ? "Distribution is based on a downsampled display, not the full dataset. " : ""}
        Descriptive visualization only; no differential expression test or FDR is implied.
      </p>
    </section>
  );
}
