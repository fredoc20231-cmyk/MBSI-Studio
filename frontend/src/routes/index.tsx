import { createFileRoute } from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronLeft,
  Columns2,
  Grid2X2,
  Image,
  LayoutGrid,
  Maximize2,
  Minus,
  Plus,
  Scan,
} from "lucide-react";
import { useState } from "react";
import { EmptyState, Workspace } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Explore spatial tissue maps — MBSI Studio" },
      {
        name: "description",
        content:
          "Explore spatial transcriptomics samples, tissue maps, gene expression and cellular neighborhoods in MBSI Studio.",
      },
      { property: "og:title", content: "Explore spatial tissue maps — MBSI Studio" },
      {
        property: "og:description",
        content:
          "An integrated workspace for spatial tissue maps, gene expression and sample comparison.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Explore,
});

const VIEW_TABS = [
  "Spatial",
  "Feature Plot",
  "Cluster",
  "Domain",
  "Niche",
  "Interaction",
  "Trajectory",
];

function Explore() {
  const [activeTab, setActiveTab] = useState("Spatial");
  const [grouping, setGrouping] = useState("By Sample");

  return (
    <Workspace>
      <h1 className="sr-only">Explore spatial tissue maps</h1>
      <div className="flex h-full min-h-[520px] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-panel">
        <div
          className="scrollbar-thin flex h-12 shrink-0 items-end gap-6 overflow-x-auto border-b border-border px-4"
          role="tablist"
          aria-label="Spatial visualizations"
        >
          {VIEW_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`relative h-12 shrink-0 text-[13px] font-medium after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:rounded-t-full after:bg-primary after:transition-transform ${
                activeTab === tab
                  ? "text-primary after:scale-x-100"
                  : "text-muted-foreground after:scale-x-0 hover:text-foreground"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-1 2xl:grid-cols-[minmax(0,1.18fr)_minmax(330px,0.82fr)]">
          <section
            aria-label={`${activeTab} tissue canvas`}
            className="flex min-h-[420px] min-w-0 flex-col border-b border-border 2xl:border-b-0 2xl:border-r"
          >
            <div className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-3">
              <div className="flex min-w-0 items-center gap-2">
                <button
                  type="button"
                  aria-label="Previous sample"
                  disabled
                  className="rounded-md border border-border p-1.5 text-muted-foreground disabled:opacity-40"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <div className="relative min-w-0">
                  <select
                    aria-label="Selected sample"
                    className="h-8 w-48 max-w-full appearance-none rounded-lg border border-input bg-background px-3 pr-8 text-xs text-muted-foreground outline-none"
                    defaultValue="none"
                  >
                    <option value="none">No sample selected</option>
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-2 top-2 h-4 w-4 text-muted-foreground" />
                </div>
              </div>
              <div className="flex items-center gap-1">
                {[Scan, Minus, Plus, Maximize2].map((Icon, index) => (
                  <button
                    key={index}
                    type="button"
                    aria-label={["Fit tissue", "Zoom out", "Zoom in", "Full screen"][index]}
                    disabled
                    className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted disabled:opacity-40"
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                ))}
              </div>
            </div>
            <div className="min-h-0 flex-1 p-3">
              <EmptyState
                title={`No ${activeTab.toLowerCase()} view loaded`}
                body="Upload a Visium, Visium HD or Xenium dataset. Observed tissue coordinates and expression values will be rendered here."
                icon={<Image className="h-6 w-6" strokeWidth={1.5} />}
                action={<UploadButton label="Upload spatial dataset" />}
              />
            </div>
          </section>

          <section aria-label="Sample comparison" className="flex min-h-[360px] min-w-0 flex-col">
            <div className="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-border px-4">
              <div
                className="flex h-full items-end gap-5"
                role="tablist"
                aria-label="Comparison grouping"
              >
                {["By Sample", "By Condition"].map((item) => (
                  <button
                    key={item}
                    type="button"
                    role="tab"
                    aria-selected={grouping === item}
                    onClick={() => setGrouping(item)}
                    className={`relative h-full text-xs font-medium after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary ${grouping === item ? "text-primary after:scale-x-100" : "text-muted-foreground after:scale-x-0"}`}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                {[Grid2X2, Columns2, LayoutGrid].map((Icon, index) => (
                  <button
                    key={index}
                    type="button"
                    aria-label={["Two-column grid", "Single-column grid", "Compact grid"][index]}
                    className={`rounded-md p-1.5 hover:bg-muted ${index === 0 ? "bg-accent text-primary" : ""}`}
                  >
                    <Icon className="h-4 w-4" />
                  </button>
                ))}
              </div>
            </div>
            <div className="grid min-h-0 flex-1 grid-cols-2 gap-2 p-3">
              {[1, 2, 3, 4].map((slot) => (
                <div
                  key={slot}
                  className="flex min-h-32 flex-col overflow-hidden rounded-lg border border-border bg-card"
                >
                  <div className="border-b border-border px-3 py-2 text-left text-[11px] font-medium text-muted-foreground">
                    Sample preview
                  </div>
                  <div className="map-grid flex flex-1 flex-col items-center justify-center bg-panel-subtle/35 p-3 text-center text-muted-foreground">
                    <Image className="mb-2 h-6 w-6" strokeWidth={1.3} />
                    <span className="text-[10px]">Awaiting sample</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </Workspace>
  );
}
