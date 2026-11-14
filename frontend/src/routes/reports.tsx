import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { mbsi } from "@/lib/mbsi-api";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Reports — MBSI Studio" },
      { name: "description", content: "Results, findings and evidence with full analysis provenance." },
      { property: "og:title", content: "Reports — MBSI Studio" },
      { property: "og:description", content: "Results, findings and evidence with full analysis provenance." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Reports,
});

function Block({ name, fn }: { name: string; fn: () => Promise<unknown> }) {
  const q = useQuery({ queryKey: [name], queryFn: fn, retry: false });
  return (
    <div className="rounded-lg border border-border p-4">
      <h2 className="mb-2 font-medium">{name}</h2>
      {q.isSuccess ? (
        <pre className="max-h-64 overflow-auto font-mono text-xs">{JSON.stringify(q.data, null, 2)}</pre>
      ) : (
        <p className="text-sm text-muted-foreground">{q.isLoading ? "Loading…" : "Unavailable from backend."}</p>
      )}
    </div>
  );
}

function Reports() {
  return (
    <Workspace>
      <h1 className="mb-4 text-xl font-semibold">Reports</h1>
      <div className="grid gap-4 lg:grid-cols-3">
        <Block name="Results" fn={mbsi.results} />
        <Block name="Findings" fn={mbsi.findings} />
        <Block name="Evidence" fn={mbsi.evidence} />
      </div>
      <div className="mt-4 h-40">
        <EmptyState title="Reports reflect observed outputs only" body="Nothing is shown as computed until the backend returns real results." />
      </div>
    </Workspace>
  );
}
