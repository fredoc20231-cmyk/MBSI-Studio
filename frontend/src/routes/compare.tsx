import { createFileRoute } from "@tanstack/react-router";
import { Columns2, GitCompare, Rows2 } from "lucide-react";
import { useState } from "react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare spatial samples — MBSI Studio" },
      {
        name: "description",
        content:
          "Compare spatial omics samples and conditions side by side with synchronized visualization controls.",
      },
      { property: "og:title", content: "Compare spatial samples — MBSI Studio" },
      {
        property: "og:description",
        content: "Side-by-side comparison of observed spatial samples and experimental conditions.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Compare,
});

function Compare() {
  const [grouping, setGrouping] = useState("Sample");
  const [layout, setLayout] = useState("Columns");

  return (
    <Workspace>
      <PageHeader
        title="Compare samples"
        description="Synchronize spatial views across observed samples or experimental conditions."
        action={<UploadButton label="Add sample" />}
      />
      <div className="flex min-h-[500px] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-panel">
        <div className="flex h-12 shrink-0 items-center justify-between border-b border-border px-4">
          <div className="flex rounded-lg bg-muted p-0.5">
            {["Sample", "Condition"].map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setGrouping(item)}
                aria-pressed={grouping === item}
                className={`rounded-md px-3 py-1.5 text-xs font-medium ${grouping === item ? "bg-card text-primary shadow-sm" : "text-muted-foreground"}`}
              >
                By {item}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            <button
              type="button"
              aria-label="Column comparison"
              onClick={() => setLayout("Columns")}
              className={`rounded-md p-2 ${layout === "Columns" ? "bg-accent text-primary" : "text-muted-foreground"}`}
            >
              <Columns2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="Row comparison"
              onClick={() => setLayout("Rows")}
              className={`rounded-md p-2 ${layout === "Rows" ? "bg-accent text-primary" : "text-muted-foreground"}`}
            >
              <Rows2 className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div
          className={`grid min-h-0 flex-1 gap-3 p-3 ${layout === "Columns" ? "md:grid-cols-2" : "grid-cols-1"}`}
        >
          {["A", "B"].map((panel) => (
            <div key={panel} className="flex min-h-52 flex-col rounded-xl border border-border p-3">
              <div className="mb-3 flex items-center justify-between text-xs">
                <span className="font-semibold">
                  {grouping} {panel}
                </span>
                <span className="text-muted-foreground">Not selected</span>
              </div>
              <EmptyState
                title="No sample selected"
                body="Choose an uploaded sample to populate this synchronized view."
                icon={<GitCompare className="h-6 w-6" strokeWidth={1.5} />}
              />
            </div>
          ))}
        </div>
      </div>
    </Workspace>
  );
}
