import { createFileRoute } from "@tanstack/react-router";
import { Database, GitMerge, Layers3, Workflow } from "lucide-react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/integrate")({
  head: () => ({
    meta: [
      { title: "Integrate spatial datasets — MBSI Studio" },
      {
        name: "description",
        content:
          "Prepare and integrate Visium, Visium HD and Xenium datasets in a transparent spatial workflow.",
      },
      { property: "og:title", content: "Integrate spatial datasets — MBSI Studio" },
      {
        property: "og:description",
        content:
          "A structured workspace for multi-sample and multi-platform spatial data integration.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Integrate,
});

const STEPS = [
  {
    number: "01",
    title: "Add datasets",
    body: "Upload observed spatial datasets and identify their platforms.",
    icon: Database,
  },
  {
    number: "02",
    title: "Align features",
    body: "Review shared features, samples and integration parameters.",
    icon: Layers3,
  },
  {
    number: "03",
    title: "Run integration",
    body: "Submit the configured workflow and inspect returned diagnostics.",
    icon: GitMerge,
  },
];

function Integrate() {
  return (
    <Workspace>
      <PageHeader
        title="Dataset integration"
        description="Bring multiple spatial samples and platforms into one traceable analysis workflow."
        action={<UploadButton />}
      />
      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step) => {
          const Icon = step.icon;
          return (
            <section
              key={step.number}
              className="rounded-xl border border-border bg-card p-5 shadow-panel"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-primary">
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </span>
                <span className="font-mono text-xs text-muted-foreground">{step.number}</span>
              </div>
              <h2 className="mt-4 text-sm font-semibold">{step.title}</h2>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{step.body}</p>
            </section>
          );
        })}
      </div>
      <div className="mt-4 h-[310px]">
        <EmptyState
          title="No integration configured"
          body="Add at least two observed datasets to begin. Compatibility checks and integration outputs come from the scientific backend."
          icon={<Workflow className="h-6 w-6" strokeWidth={1.5} />}
          action={<UploadButton label="Add first dataset" />}
        />
      </div>
    </Workspace>
  );
}
