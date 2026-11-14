import { createFileRoute } from "@tanstack/react-router";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/analyze")({
  head: () => ({
    meta: [
      { title: "Analyze — MBSI Studio" },
      { name: "description", content: "Run spatial transcriptomics workflows: segmentation, clustering and spatialGE analyses." },
      { property: "og:title", content: "Analyze — MBSI Studio" },
      { property: "og:description", content: "Run spatial transcriptomics workflows: segmentation, clustering and spatialGE analyses." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <Workspace>
      <h1 className="mb-4 text-xl font-semibold">Analyze</h1>
      <div className="h-[60vh]">
        <EmptyState title="Nothing to show yet" body="No workflow runs yet. Upload a dataset, then start a workflow from the backend." action={<UploadButton />} />
      </div>
    </Workspace>
  ),
});
