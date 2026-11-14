import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Aperture,
  BarChart3,
  Bell,
  ChevronDown,
  CircleHelp,
  FileText,
  GitCompare,
  Hexagon,
  Image,
  Layers3,
  Map,
  Microscope,
  MoreHorizontal,
  Network,
  PanelLeftOpen,
  PanelRightOpen,
  Plus,
  Route,
  Search,
  Tag,
  UserRound,
  Workflow,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { AnalysisDock } from "@/components/mbsi/AnalysisDock";
import { UploadButton } from "@/components/mbsi/UploadButton";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { API_URL, mbsi } from "@/lib/mbsi-api";

const NAV = [
  { to: "/", label: "Explore", icon: Map },
  { to: "/analyze", label: "Analyze", icon: BarChart3 },
  { to: "/compare", label: "Compare", icon: GitCompare },
  { to: "/integrate", label: "Integrate", icon: Workflow },
  { to: "/annotation", label: "Annotation", icon: Tag },
  { to: "/imaging", label: "Imaging", icon: Image },
  { to: "/reports", label: "Reports", icon: FileText },
] satisfies ReadonlyArray<{ to: string; label: string; icon: LucideIcon }>;

const VIEWS = [
  { label: "Expression", icon: BarChart3 },
  { label: "Clusters", icon: Hexagon },
  { label: "Domains", icon: Layers3 },
  { label: "Niches", icon: Network },
  { label: "Cell interaction", icon: GitCompare },
  { label: "Trajectories", icon: Route },
  { label: "Spatial stats", icon: MoreHorizontal },
];

function ApiStatus({ compact = false }: { compact?: boolean }) {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: mbsi.health,
    retry: false,
    refetchInterval: 30000,
  });
  const connected = query.isSuccess;
  const label = query.isLoading
    ? "Checking backend"
    : connected
      ? "Backend connected"
      : "Backend unavailable";

  return (
    <div
      className="flex items-center gap-2 text-xs text-muted-foreground"
      title={`${label} · ${API_URL}`}
    >
      <span
        className={`h-2 w-2 shrink-0 rounded-full ${connected ? "bg-success" : query.isLoading ? "bg-warning" : "bg-destructive"}`}
        aria-hidden
      />
      {!compact && <span className="hidden 2xl:inline">{label}</span>}
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
  icon,
}: {
  title: string;
  body: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="map-grid flex h-full min-h-44 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-panel-subtle/45 p-7 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-card text-primary shadow-panel">
        {icon ?? <Microscope className="h-6 w-6" strokeWidth={1.5} />}
      </div>
      <div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-muted-foreground">{body}</p>
      </div>
      {action}
    </div>
  );
}

export function Panel({
  title,
  children,
  className = "",
  action,
}: {
  title: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}) {
  return (
    <section
      aria-label={title}
      className={`flex min-h-0 flex-col border-border bg-card ${className}`}
    >
      <div className="flex h-11 shrink-0 items-center justify-between border-b border-border px-4">
        <h2 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground">
          {title}
        </h2>
        {action}
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-4">{children}</div>
    </section>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-1 max-w-2xl text-xs leading-5 text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

function SidebarSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details open className="group border-b border-border last:border-b-0">
      <summary className="flex h-11 cursor-pointer list-none items-center justify-between px-4 text-sm font-semibold marker:hidden [&::-webkit-details-marker]:hidden">
        {title}
        <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-180" />
      </summary>
      <div className="px-3 pb-4">{children}</div>
    </details>
  );
}

function StudySidebar({ gene, setGene }: { gene: string; setGene: (value: string) => void }) {
  const [view, setView] = useState("Expression");
  const [scale, setScale] = useState("Auto");
  const [spotSize, setSpotSize] = useState(55);

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-card">
      <SidebarSection title="Study">
        <label className="sr-only" htmlFor="study-select">
          Study
        </label>
        <div className="relative">
          <select
            id="study-select"
            className="h-9 w-full appearance-none rounded-lg border border-input bg-background px-3 pr-8 text-xs text-foreground outline-none focus:ring-2 focus:ring-ring"
            defaultValue="none"
          >
            <option value="none">No study selected</option>
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        </div>
      </SidebarSection>

      <SidebarSection title="Samples (0)">
        <div className="rounded-lg border border-dashed border-border px-3 py-4 text-center text-xs text-muted-foreground">
          Uploaded samples will appear here.
        </div>
        <UploadButton
          label="Add sample"
          variant="ghost"
          className="mt-2 h-8 w-full justify-start px-2 text-primary hover:bg-accent"
        />
      </SidebarSection>

      <SidebarSection title="View">
        <div className="space-y-0.5" role="list" aria-label="Spatial views">
          {VIEWS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                onClick={() => setView(item.label)}
                aria-pressed={view === item.label}
                className={`flex h-8 w-full items-center gap-2.5 rounded-lg px-2.5 text-left text-xs transition-colors ${
                  view === item.label
                    ? "bg-accent font-medium text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" strokeWidth={1.6} />
                {item.label}
              </button>
            );
          })}
        </div>
      </SidebarSection>

      <SidebarSection title="Gene">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={gene}
            onChange={(event) => setGene(event.target.value)}
            placeholder="Search gene"
            aria-label="Search gene"
            className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-8 text-xs outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
          />
          {gene && (
            <button
              type="button"
              onClick={() => setGene("")}
              aria-label="Clear gene"
              className="absolute right-2 top-2 rounded p-0.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </SidebarSection>

      <SidebarSection title="Display">
        <div className="space-y-4 px-1">
          <div>
            <label htmlFor="color-scale" className="mb-1.5 block text-xs text-muted-foreground">
              Color scale
            </label>
            <div className="relative">
              <select
                id="color-scale"
                className="h-9 w-full appearance-none rounded-lg border border-input bg-background px-3 pr-8 text-xs outline-none focus:ring-2 focus:ring-ring"
                defaultValue="viridis"
              >
                <option value="viridis">Viridis</option>
                <option value="magma">Magma</option>
                <option value="cividis">Cividis</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            </div>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted-foreground">Scale</span>
            <div className="flex rounded-lg border border-border bg-muted p-0.5">
              {["Auto", "Fixed"].map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setScale(item)}
                  aria-pressed={scale === item}
                  className={`rounded-md px-3 py-1 text-[11px] ${scale === item ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground"}`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>Spot size</span>
              <span>{spotSize}%</span>
            </div>
            <input
              type="range"
              aria-label="Spot size"
              min={10}
              max={100}
              step={1}
              value={spotSize}
              onChange={(event) => setSpotSize(Number(event.target.value))}
              className="spot-size-slider"
              style={{
                background: `linear-gradient(to right, var(--primary) ${spotSize}%, var(--accent) ${spotSize}%)`,
              }}
            />
          </div>
        </div>
      </SidebarSection>
    </div>
  );
}

function FeatureInspector({ gene }: { gene: string }) {
  const [tab, setTab] = useState("Gene Info");
  return (
    <div className="flex h-full flex-col bg-card">
      <div
        className="flex h-12 shrink-0 items-end gap-5 border-b border-border px-4"
        role="tablist"
        aria-label="Feature details"
      >
        {["Gene Info", "Markers", "Results"].map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={tab === item}
            onClick={() => setTab(item)}
            className={`relative h-12 text-[13px] font-medium after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-primary after:transition-transform ${tab === item ? "text-primary after:scale-x-100" : "text-muted-foreground after:scale-x-0 hover:text-foreground"}`}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        <div className="border-b border-border pb-4">
          <h2 className="truncate text-2xl font-semibold tracking-tight">
            {gene || "No gene selected"}
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {gene
              ? "Awaiting observed feature information"
              : "Search for a gene in the study panel"}
          </p>
        </div>
        {tab === "Gene Info" && (
          <>
            <section className="border-b border-border py-4">
              <h3 className="mb-3 flex items-center justify-between text-sm font-semibold">
                Expression <ChevronDown className="h-4 w-4" />
              </h3>
              <div className="flex h-44 flex-col items-center justify-center rounded-xl border border-dashed border-border bg-panel-subtle/50 px-4 text-center">
                <BarChart3 className="mb-2 h-7 w-7 text-muted-foreground" strokeWidth={1.4} />
                <p className="text-xs font-medium">No expression data</p>
                <p className="mt-1 text-[11px] leading-4 text-muted-foreground">
                  Upload and analyze a dataset to view sample distributions.
                </p>
              </div>
            </section>
            <section className="py-4">
              <h3 className="mb-3 flex items-center justify-between text-sm font-semibold">
                Statistics <ChevronDown className="h-4 w-4" />
              </h3>
              <dl className="overflow-hidden rounded-lg border border-border text-xs">
                {["log₂FC", "FDR", "% spots (group A)", "% spots (group B)"].map((label) => (
                  <div
                    key={label}
                    className="flex items-center justify-between border-b border-border px-3 py-2 last:border-b-0 odd:bg-panel-subtle/60"
                  >
                    <dt className="text-muted-foreground">{label}</dt>
                    <dd className="font-mono">—</dd>
                  </div>
                ))}
              </dl>
            </section>
          </>
        )}
        {tab === "Markers" && (
          <EmptyState
            title="No markers returned"
            body="Marker genes will appear here after the backend returns observed marker results."
          />
        )}
        {tab === "Results" && (
          <EmptyState
            title="No results returned"
            body="Feature-level results and their analysis provenance will appear here."
          />
        )}
      </div>
    </div>
  );
}

function CustomInspector({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full flex-col bg-card">
      <div className="flex h-12 shrink-0 items-center border-b border-border px-4">
        <h2 className="text-sm font-semibold">Selection inspector</h2>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-4">{children}</div>
    </div>
  );
}

export function Workspace({
  children,
  inspector,
  dock,
}: {
  children: ReactNode;
  inspector?: ReactNode;
  dock?: ReactNode;
}) {
  const [gene, setGene] = useState("");
  const sidebar = <StudySidebar gene={gene} setGene={setGene} />;
  const inspectorContent = inspector ? (
    <CustomInspector>{inspector}</CustomInspector>
  ) : (
    <FeatureInspector gene={gene} />
  );

  return (
    <div className="flex h-dvh min-h-[620px] flex-col overflow-hidden bg-workspace text-foreground">
      <header className="flex h-[68px] shrink-0 items-center border-b border-border bg-card pr-3 shadow-panel">
        <Link
          to="/"
          className="flex h-full w-[218px] shrink-0 items-center gap-2.5 px-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring lg:w-[240px]"
        >
          <Aperture className="h-10 w-10 text-primary" strokeWidth={2.1} aria-hidden />
          <span className="leading-none">
            <span className="block text-[25px] font-bold tracking-tight">
              <span className="text-primary">MBSI</span>{" "}
              <span className="font-normal text-foreground">Studio</span>
            </span>
            <span className="mt-1 hidden text-[10px] tracking-wide text-muted-foreground sm:block">
              Spatial Omics Platform
            </span>
          </span>
        </Link>
        <nav
          aria-label="Main"
          className="scrollbar-thin hidden h-full min-w-0 flex-1 items-stretch justify-center overflow-x-auto lg:flex"
        >
          {NAV.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                activeOptions={{ exact: true }}
                className="relative flex shrink-0 items-center gap-2 border-b-2 border-transparent px-3 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring xl:px-4 xl:text-sm"
                activeProps={{ className: "border-primary text-primary" }}
              >
                <Icon className="h-[18px] w-[18px]" strokeWidth={1.7} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto flex items-center gap-1 pl-2">
          <ApiStatus compact />
          <a
            href="https://github.com/fredoc20231-cmyk/MBSI-Studio"
            target="_blank"
            rel="noreferrer"
            aria-label="Open MBSI Studio documentation"
            className="hidden h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:flex"
          >
            <CircleHelp className="h-[19px] w-[19px]" strokeWidth={1.7} />
          </a>
          <button
            type="button"
            aria-label="Notifications"
            onClick={() => toast.info("No new notifications")}
            className="hidden h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:flex"
          >
            <Bell className="h-[19px] w-[19px]" strokeWidth={1.7} />
          </button>
          <button
            type="button"
            aria-label="Workspace information"
            onClick={() =>
              toast.info("Local analysis workspace", {
                description: "Sign-in profiles are not connected.",
              })
            }
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <UserRound className="h-[19px] w-[19px]" strokeWidth={1.7} />
          </button>
        </div>
      </header>

      <nav
        aria-label="Mobile main"
        className="scrollbar-thin flex h-11 shrink-0 items-stretch overflow-x-auto border-b border-border bg-card px-2 lg:hidden"
      >
        {NAV.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: true }}
              className="flex shrink-0 items-center gap-1.5 border-b-2 border-transparent px-3 text-xs font-medium text-muted-foreground"
              activeProps={{ className: "border-primary text-primary" }}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-[240px] shrink-0 border-r border-border bg-card lg:block">
          {sidebar}
        </aside>
        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex h-11 shrink-0 items-center justify-between border-b border-border bg-card px-3 lg:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
                >
                  <PanelLeftOpen className="h-4 w-4" /> Study & display
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[290px] p-0">
                <SheetTitle className="sr-only">Study and display controls</SheetTitle>
                <SheetDescription className="sr-only">
                  Choose views, search genes, and adjust display settings.
                </SheetDescription>
                {sidebar}
              </SheetContent>
            </Sheet>
            <Sheet>
              <SheetTrigger asChild>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted"
                >
                  <PanelRightOpen className="h-4 w-4" /> Inspector
                </button>
              </SheetTrigger>
              <SheetContent side="right" className="w-[330px] max-w-[90vw] p-0">
                <SheetTitle className="sr-only">Feature inspector</SheetTitle>
                <SheetDescription className="sr-only">
                  Inspect genes, markers, and observed results.
                </SheetDescription>
                {inspectorContent}
              </SheetContent>
            </Sheet>
          </div>
          <div className="scrollbar-thin min-h-0 flex-1 overflow-auto p-3">{children}</div>
          {dock ? (
            <section
              aria-label="Analysis status"
              className="max-h-52 shrink-0 overflow-auto border-t border-border bg-card p-4"
            >
              {dock}
            </section>
          ) : (
            <AnalysisDock />
          )}
        </main>
        <aside className="hidden w-[336px] shrink-0 border-l border-border bg-card xl:block">
          {inspectorContent}
        </aside>
      </div>
    </div>
  );
}
