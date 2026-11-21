import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Microscope, Play, ShieldCheck } from "lucide-react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";
import { mbsi, type DatasetUploadResponse, type WorkflowRunResponse } from "@/lib/mbsi-api";
import { PHASE_NOTES, VISIUM_MODULES, isBlocked } from "@/lib/visium-modules";

export const Route = createFileRoute("/visium")({
  head: () => ({
    meta: [
      { title: "Visium workflow — MBSI Studio" },
      { name: "description", content: "Spatially variable genes, niches, deconvolution, replicate-aware DE, cell interactions and Visium HD with provenance." },
      { property: "og:title", content: "Visium workflow — MBSI Studio" },
      { property: "og:description", content: "Guardrailed Visium and Visium HD analysis with traceable provenance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Visium,
});

function Visium() {
  const caps = useQuery({ queryKey: ["capabilities"], queryFn: mbsi.capabilities, retry: false });
  const datasets = useQuery<DatasetUploadResponse[]>({ queryKey: ["uploaded-datasets"], queryFn: () => [], initialData: [], enabled: false }).data;
  const [datasetId, setDatasetId] = useState("");
  const [runs, setRuns] = useState<Record<string, WorkflowRunResponse | string>>({});
  const [busy, setBusy] = useState("");
  const active = datasetId || datasets[0]?.dataset_id || "";

  async function run(module: string, params: Record<string, unknown>) {
    setBusy(module);
    try {
      const res = await mbsi.runWorkflow({ dataset_id: active, module, params, allow_demo: false });
      setRuns((r) => ({ ...r, [module]: res }));
    } catch (e) {
      setRuns((r) => ({ ...r, [module]: e instanceof Error ? e.message : String(e) }));
    } finally {
      setBusy("");
    }
  }

  return (
    <Workspace>
      <PageHeader
        title="Visium workflow"
        description="Standard Visium and Visium HD analyses run on the scientific service. Missing data, replicates or libraries show as blocked, never substituted."
        action={<UploadButton />}
      />
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted-foreground">Dataset</span>
        <select aria-label="Dataset" value={active} onChange={(e) => setDatasetId(e.target.value)} className="h-8 rounded-lg border border-border bg-card px-2">
          {datasets.length === 0 && <option value="">No uploaded dataset</option>}
          {datasets.map((d) => <option key={d.dataset_id} value={d.dataset_id}>{d.dataset_id}</option>)}
        </select>
        <span className="text-muted-foreground">
          {caps.isSuccess ? "Backend capabilities loaded" : caps.isLoading ? "Checking backend capabilities…" : "Backend capabilities unavailable"}
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
        {VISIUM_MODULES.map((m) => {
          const cap = caps.data?.modules.find((c) => c.module === m.module);
          const result = runs[m.module];
          const ready = Boolean(cap?.installed && active);
          return (
            <section key={m.module} className="flex flex-col rounded-xl border border-border bg-card p-4 shadow-panel">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Phase {m.phase}</span>
                <span>{cap ? (cap.installed ? `Ready · ${cap.evidence_tier.replace("_", " ")}` : "Libraries missing on service") : "Unavailable"}</span>
              </div>
              <h2 className="mt-2 text-sm font-semibold">{m.title}</h2>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{m.description}</p>
              <button type="button" disabled={!ready || busy === m.module} onClick={() => run(m.module, m.params)} className="mt-3 inline-flex h-8 w-fit items-center gap-2 rounded-lg bg-primary px-3 text-xs font-medium text-primary-foreground disabled:opacity-50">
                <Play className="h-3.5 w-3.5" /> {busy === m.module ? "Running…" : "Run"}
              </button>
              {result && (
                <div className="mt-3 rounded-lg bg-panel-subtle p-2 text-[11px]">
                  {typeof result === "string" ? (
                    <p className="text-destructive">{result}</p>
                  ) : isBlocked(result.outputs) ? (
                    <p><strong>Blocked:</strong> {String(result.outputs["blocked_reason"])} {String(result.outputs["requirement"] ?? "")}</p>
                  ) : (
                    <pre className="scrollbar-thin max-h-48 overflow-auto whitespace-pre-wrap font-mono">{JSON.stringify(result.outputs, null, 2)}</pre>
                  )}
                </div>
              )}
            </section>
          );
        })}
        {PHASE_NOTES.map((n) => (
          <section key={n.phase} className="rounded-xl border border-dashed border-border bg-card p-4">
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground"><ShieldCheck className="h-3.5 w-3.5" /> Phase {n.phase}</div>
            <h2 className="mt-2 text-sm font-semibold">{n.title}</h2>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">{n.body}</p>
          </section>
        ))}
      </div>
      {datasets.length === 0 && (
        <div className="mt-4 h-44">
          <EmptyState title="No Visium dataset yet" body="Upload Space Ranger output (Visium or Visium HD) to run these analyses." icon={<Microscope className="h-6 w-6" strokeWidth={1.5} />} action={<UploadButton label="Choose dataset" variant="outline" />} />
        </div>
      )}
    </Workspace>
  );
}
