import { createFileRoute } from "@tanstack/react-router";
import { Brush, Layers3, MousePointer2, Pentagon, Redo2, Tag, Undo2 } from "lucide-react";
import { useState } from "react";
import { EmptyState, PageHeader, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/annotation")({
  head: () => ({
    meta: [
      { title: "Annotate spatial regions — MBSI Studio" },
      {
        name: "description",
        content:
          "Review and annotate spatial regions, domains and cell types on observed tissue maps.",
      },
      { property: "og:title", content: "Annotate spatial regions — MBSI Studio" },
      {
        property: "og:description",
        content: "A focused annotation canvas for spatial regions, tissue domains and cell types.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Annotation,
});

const TOOLS = [
  { name: "Select", icon: MousePointer2 },
  { name: "Brush", icon: Brush },
  { name: "Polygon", icon: Pentagon },
  { name: "Labels", icon: Tag },
];

function Annotation() {
  const [tool, setTool] = useState("Select");

  return (
    <Workspace>
      <PageHeader
        title="Spatial annotation"
        description="Select regions and organize biological labels directly on an observed tissue map."
        action={<UploadButton />}
      />
      <div className="flex min-h-[500px] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-panel">
        <div className="flex h-12 shrink-0 items-center justify-between border-b border-border px-3">
          <div className="flex items-center gap-1" role="toolbar" aria-label="Annotation tools">
            {TOOLS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.name}
                  type="button"
                  onClick={() => setTool(item.name)}
                  aria-pressed={tool === item.name}
                  className={`inline-flex h-8 items-center gap-2 rounded-lg px-3 text-xs font-medium ${tool === item.name ? "bg-accent text-primary" : "text-muted-foreground hover:bg-muted"}`}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </button>
              );
            })}
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              aria-label="Undo annotation"
              disabled
              className="rounded-md p-2 text-muted-foreground disabled:opacity-40"
            >
              <Undo2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="Redo annotation"
              disabled
              className="rounded-md p-2 text-muted-foreground disabled:opacity-40"
            >
              <Redo2 className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="grid min-h-0 flex-1 md:grid-cols-[1fr_210px]">
          <div className="min-h-80 p-3">
            <EmptyState
              title="No tissue map loaded"
              body={`The ${tool.toLowerCase()} tool is ready. Upload a spatial dataset before creating annotations.`}
              action={<UploadButton label="Load tissue map" />}
            />
          </div>
          <aside className="border-t border-border p-4 md:border-l md:border-t-0">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <Layers3 className="h-4 w-4 text-primary" /> Annotation layers
            </h2>
            <div className="mt-4 rounded-lg border border-dashed border-border p-4 text-center text-xs leading-5 text-muted-foreground">
              Region and cell-type layers will appear here.
            </div>
          </aside>
        </div>
      </div>
    </Workspace>
  );
}
