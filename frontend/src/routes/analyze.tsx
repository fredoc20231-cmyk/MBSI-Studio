import { createFileRoute } from "@tanstack/react-router";
import { ArrowUpRight, FlaskConical } from "lucide-react";
import { ANALYSIS_TOOLS } from "@/components/mbsi/AnalysisDock";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/analyze")({
  head: () => ({
    meta: [
      { title: "Spatial analysis workflows — MBSI Studio" },
      {
        name: "description",
        content:
          "Configure spatial clustering, differential expression, enrichment, niches and heterogeneity workflows.",
      },
      { property: "og:title", content: "Spatial analysis workflows — MBSI Studio" },
      {
        property: "og:description",
        content: "A unified studio for observed spatial omics analysis workflows and provenance.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Analyze,
});

function Analyze() {
  return (
    <Workspace>
      <PageHeader
        title="Analysis studio"
        description="Choose a spatial workflow, configure its parameters and review backend-returned outputs with their provenance."
        action={<UploadButton />}
      />
      <div className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-3">
        {ANALYSIS_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <section
              key={tool.name}
              className="group rounded-xl border border-border bg-card p-4 shadow-panel transition-colors hover:border-primary/30"
            >
              <div className="flex items-start justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-primary">
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </span>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-primary" />
              </div>
              <h2 className="mt-4 text-sm font-semibold">{tool.name}</h2>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{tool.description}</p>
              <div className="mt-4 border-t border-border pt-3 text-[11px] text-muted-foreground">
                Observed dataset required
              </div>
            </section>
          );
        })}
      </div>
      <div className="mt-4 h-52">
        <EmptyState
          title="No workflow runs yet"
          body="Upload an observed dataset to configure a workflow. Run status, parameters and outputs will appear here."
          icon={<FlaskConical className="h-6 w-6" strokeWidth={1.5} />}
          action={<UploadButton label="Choose dataset" variant="outline" />}
        />
      </div>
    </Workspace>
  );
}
