import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Download, FileCheck2, FileText, FlaskConical, Library } from "lucide-react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { mbsi } from "@/lib/mbsi-api";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Results and evidence reports — MBSI Studio" },
      {
        name: "description",
        content:
          "Review observed spatial omics results, biological findings and supporting evidence with analysis provenance.",
      },
      { property: "og:title", content: "Results and evidence reports — MBSI Studio" },
      {
        property: "og:description",
        content: "Traceable reports built from observed results, findings and supporting evidence.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Reports,
});

function ReportBlock({
  name,
  description,
  fn,
  icon: Icon,
}: {
  name: string;
  description: string;
  fn: () => Promise<unknown>;
  icon: typeof FileText;
}) {
  const query = useQuery({ queryKey: [name], queryFn: fn, retry: false });
  return (
    <section className="flex min-h-64 flex-col rounded-xl border border-border bg-card p-4 shadow-panel">
      <div className="flex items-start gap-3 border-b border-border pb-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-primary">
          <Icon className="h-5 w-5" strokeWidth={1.6} />
        </span>
        <div>
          <h2 className="text-sm font-semibold">{name}</h2>
          <p className="mt-1 text-[11px] leading-4 text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="min-h-0 flex-1 pt-4">
        {query.isSuccess ? (
          <pre className="scrollbar-thin max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-panel-subtle p-3 font-mono text-[11px] leading-5">
            {JSON.stringify(query.data, null, 2)}
          </pre>
        ) : (
          <div className="flex h-36 flex-col items-center justify-center rounded-lg border border-dashed border-border text-center">
            <FileText className="mb-2 h-6 w-6 text-muted-foreground" strokeWidth={1.4} />
            <p className="text-xs font-medium">
              {query.isLoading
                ? `Loading ${name.toLowerCase()}…`
                : `No ${name.toLowerCase()} available`}
            </p>
            {!query.isLoading && (
              <p className="mt-1 text-[11px] text-muted-foreground">
                The scientific backend did not return data.
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function Reports() {
  return (
    <Workspace>
      <PageHeader
        title="Reports & evidence"
        description="Review observed outputs, synthesized findings and their supporting evidence without losing analysis provenance."
        action={
          <button
            type="button"
            disabled
            className="inline-flex h-8 items-center gap-2 rounded-lg border border-border bg-card px-3 text-xs font-medium text-muted-foreground opacity-50"
          >
            <Download className="h-4 w-4" /> Export report
          </button>
        }
      />
      <div className="grid gap-3 2xl:grid-cols-3">
        <ReportBlock
          name="Results"
          description="Observed outputs returned by completed analysis workflows."
          fn={mbsi.results}
          icon={FlaskConical}
        />
        <ReportBlock
          name="Findings"
          description="Biological findings linked to their originating results."
          fn={mbsi.findings}
          icon={FileCheck2}
        />
        <ReportBlock
          name="Evidence"
          description="Supporting records and provenance for reported findings."
          fn={mbsi.evidence}
          icon={Library}
        />
      </div>
      <div className="mt-4 h-40">
        <EmptyState
          title="Reports reflect observed outputs only"
          body="Nothing is presented as computed until the scientific backend returns real results and provenance."
        />
      </div>
    </Workspace>
  );
}
