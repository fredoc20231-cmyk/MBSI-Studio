import { useState } from "react";
import { mbsi, type MorphologySTIEInput, type MorphologySTIEResult } from "@/lib/mbsi-api";

export function MorphologySTIEPanel() {
  const [input, setInput] = useState<MorphologySTIEInput | null>(null);
  const [result, setResult] = useState<MorphologySTIEResult | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function load(file: File | undefined) {
    setInput(null); setResult(null); setError("");
    if (!file) return;
    try {
      if (file.size > 10_000_000) throw new Error("JSON file must be smaller than 10 MB");
      const parsed = JSON.parse(await file.text()) as MorphologySTIEInput;
      for (const key of ["expression", "signatures", "morphology", "cell_coords", "spot_coords"] as const) {
        if (!Array.isArray(parsed[key]) || parsed[key].length === 0)
          throw new Error(`Missing nonempty ${key} matrix`);
      }
      setInput(parsed);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }

  async function run() {
    if (!input) return;
    setRunning(true); setResult(null); setError("");
    try { setResult(await mbsi.morphologySTIE(input)); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setRunning(false); }
  }

  return (
    <section className="mt-6 rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-semibold">Experimental morphology-guided reconstruction (STIE)</h2>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        Upload registered spot expression, gene-aligned reference signatures, observed nuclear
        morphology and coordinates as a JSON object. Cell assignments are probabilistic estimates,
        not measured identities. Do not upload identifiable patient data to an unauthenticated service.
      </p>
      <label className="mt-4 block text-xs font-medium" htmlFor="stie-json">Registered data (JSON)</label>
      <input id="stie-json" className="mt-2 block w-full text-xs" type="file" accept=".json,application/json"
        onChange={(event) => void load(event.target.files?.[0])} />
      <button type="button" disabled={!input || running} onClick={() => void run()}
        className="mt-4 rounded-lg bg-primary px-4 py-2 text-xs text-primary-foreground disabled:opacity-50">
        {running ? "Running inference…" : "Run experimental STIE"}
      </button>
      {error && <p role="alert" className="mt-3 text-xs text-destructive">{error}</p>}
      {result && (
        <div className="mt-4 space-y-2 text-xs" aria-live="polite">
          <p>Result: {result.status} · Validation: {result.validation_status} · Converged: {String(result.converged)}</p>
          <p>{result.cell_type_index.length} observed nuclei · {result.spot_abundance.length} spots</p>
          <p>Mean maximum assignment probability: {
            (result.cell_confidence.reduce((a, v) => a + v, 0) / Math.max(1, result.cell_confidence.length)).toFixed(3)
          }</p>
          {result.warnings.map((warning) => <p key={warning} className="text-muted-foreground">{warning}</p>)}
          <button type="button" className="rounded-lg border border-border px-3 py-2"
            onClick={() => {
              const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const anchor = document.createElement("a");
              anchor.href = url; anchor.download = "mbsi-stie-experimental.json"; anchor.click();
              URL.revokeObjectURL(url);
            }}>Export result JSON</button>
        </div>
      )}
    </section>
  );
}
