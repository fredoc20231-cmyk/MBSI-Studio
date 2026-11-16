import { Link } from "@tanstack/react-router";
import {
  ArrowUpRight,
  BarChart3,
  Blocks,
  ChartSpline,
  Grid3X3,
  Network,
  Play,
  ScatterChart,
} from "lucide-react";
import { useState, type ComponentType } from "react";

export const ANALYSIS_TOOLS = [
  { name: "STclust", description: "Spatial clustering", icon: ScatterChart },
  { name: "STdiff", description: "Spatial differential expression", icon: Blocks },
  { name: "STenrich", description: "Functional enrichment in spatial regions", icon: BarChart3 },
  { name: "STniche", description: "Spatial niche identification", icon: Network },
  { name: "STgradient", description: "Spatial expression gradients", icon: ChartSpline },
  { name: "SThet", description: "Spatial heterogeneity analysis", icon: Grid3X3 },
] satisfies Array<{
  name: string;
  description: string;
  icon: ComponentType<{ className?: string }>;
}>;

const DOCK_TABS = [
  "SpatialGE",
  "Differential",
  "Enrichment",
  "Niche",
  "Gradient",
  "STclust",
  "SThet",
  "Pseudobulk",
];

export function AnalysisDock() {
  const [activeTab, setActiveTab] = useState("SpatialGE");

  return (
    <section
      aria-label="Analysis tools"
      className="flex h-[218px] shrink-0 flex-col border-t border-border bg-card"
    >
      <div
        className="scrollbar-thin flex h-11 shrink-0 items-end gap-6 overflow-x-auto border-b border-border px-5"
        role="tablist"
        aria-label="Analysis methods"
      >
        {DOCK_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            onClick={() => setActiveTab(tab)}
            className={`relative h-11 shrink-0 text-[13px] font-medium transition-colors after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:rounded-t-full after:bg-primary after:transition-transform ${
              activeTab === tab
                ? "text-primary after:scale-x-100"
                : "text-muted-foreground after:scale-x-0 hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="scrollbar-thin flex min-h-0 flex-1 gap-3 overflow-x-auto p-3">
        <div className="flex w-[270px] shrink-0 flex-col justify-between rounded-xl border border-border bg-card p-4 shadow-panel">
          <div>
            <h2 className="text-[15px] font-semibold tracking-tight">Run {activeTab} analysis</h2>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Configure an observed dataset and run the selected workflow in the analysis studio.
            </p>
          </div>
          <Link
            to="/analyze"
            className="inline-flex h-8 w-fit items-center gap-2 rounded-lg bg-primary px-3 text-xs font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Play className="h-3.5 w-3.5" /> Open analysis
          </Link>
        </div>
        {ANALYSIS_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <Link
              key={tool.name}
              to="/analyze"
              className="group flex w-[174px] shrink-0 flex-col items-center justify-center rounded-xl border border-border bg-card px-3 py-3 text-center shadow-panel transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-float focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span className="relative flex h-9 w-12 items-center justify-center text-primary">
                <Icon className="h-8 w-8" strokeWidth={1.5} />
                <ArrowUpRight className="absolute -right-2 -top-1 h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
              </span>
              <span className="mt-2 text-sm font-semibold">{tool.name}</span>
              <span className="mt-0.5 text-[11px] leading-4 text-muted-foreground">
                {tool.description}
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
