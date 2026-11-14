import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";
import { mbsi } from "@/lib/mbsi-api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MBSI Studio — Spatial omics explorer" },
      { name: "description", content: "Explore spatial transcriptomics samples, tissue maps and genes with MBSI Studio." },
      { property: "og:title", content: "MBSI Studio — Spatial omics explorer" },
      { property: "og:description", content: "Explore spatial transcriptomics samples, tissue maps and genes." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Explore,
});

function Explore() {
  const tech = useQuery({ queryKey: ["technologies"], queryFn: mbsi.technologies, retry: false });
  return (
    <Workspace
      inspector={
        <div className="space-y-2 text-sm">
          <p className="font-medium">Supported technologies</p>
          {tech.isSuccess ? (
            <pre className="font-mono text-xs whitespace-pre-wrap">{JSON.stringify(tech.data, null, 2)}</pre>
          ) : (
            <p className="text-muted-foreground">Unavailable — backend not reachable.</p>
          )}
        </div>
      }
    >
      <h1 className="mb-4 text-xl font-semibold">Explore</h1>
      <div className="h-[60vh]">
        <EmptyState
          title="No tissue map loaded"
          body="Upload a Visium, Visium HD or Xenium dataset to view linked sample maps and gene expression."
          action={<UploadButton />}
        />
      </div>
    </Workspace>
  );
}
