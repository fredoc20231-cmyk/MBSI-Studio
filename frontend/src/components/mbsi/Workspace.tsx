import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { API_URL, mbsi } from "@/lib/mbsi-api";

const NAV = [
  { to: "/", label: "Explore" },
  { to: "/analyze", label: "Analyze" },
  { to: "/compare", label: "Compare" },
  { to: "/integrate", label: "Integrate" },
  { to: "/annotation", label: "Annotation" },
  { to: "/imaging", label: "Imaging" },
  { to: "/reports", label: "Reports" },
] as const;

function ApiStatus() {
  const q = useQuery({ queryKey: ["health"], queryFn: mbsi.health, retry: false, refetchInterval: 30000 });
  const ok = q.isSuccess;
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground" title={API_URL}>
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-primary" : "bg-destructive"}`} aria-hidden />
      {q.isLoading ? "Checking backend…" : ok ? "Backend connected" : "Backend unreachable"}
    </div>
  );
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode | undefined }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border p-8 text-center">
      <p className="font-medium text-foreground">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{body}</p>
      {action}
    </div>
  );
}

export function Panel({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section aria-label={title} className={`flex min-h-0 flex-col border-border bg-card ${className}`}>
      <h2 className="border-b border-border px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</h2>
      <div className="min-h-0 flex-1 overflow-auto p-4">{children}</div>
    </section>
  );
}

export function Workspace({
  children,
  inspector,
  dock,
}: { children: ReactNode; inspector?: ReactNode | undefined; dock?: ReactNode | undefined }) {
  const tree = useQuery({ queryKey: ["readiness"], queryFn: mbsi.readiness, retry: false });
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <header className="flex items-center gap-6 border-b border-border px-4 py-2">
        <Link to="/" className="font-semibold tracking-tight">
          MBSI <span className="text-primary">Studio</span>
        </Link>
        <nav aria-label="Main" className="flex flex-1 gap-1 overflow-x-auto">
          {NAV.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              activeOptions={{ exact: true }}
              className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              activeProps={{ className: "bg-accent text-accent-foreground font-medium" }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <ApiStatus />
      </header>
      <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[240px_1fr_280px]">
        <Panel title="Studies & samples" className="hidden border-r md:flex">
          {tree.isSuccess ? (
            <pre className="font-mono text-xs whitespace-pre-wrap">{JSON.stringify(tree.data, null, 2)}</pre>
          ) : (
            <p className="text-sm text-muted-foreground">No datasets yet. Upload a dataset to populate the study tree.</p>
          )}
        </Panel>
        <main className="flex min-h-0 flex-col">
          <div className="min-h-0 flex-1 overflow-auto p-4">{children}</div>
          <Panel title="Analysis tools" className="h-48 border-t">
            {dock ?? <p className="text-sm text-muted-foreground">No analysis jobs. Runs appear here with their status and provenance.</p>}
          </Panel>
        </main>
        <Panel title="Feature inspector" className="hidden border-l md:flex">
          {inspector ?? <p className="text-sm text-muted-foreground">Select a spot, cell or field of view to inspect its features.</p>}
        </Panel>
      </div>
    </div>
  );
}
