import { createFileRoute } from "@tanstack/react-router";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/annotation")({
  head: () => ({
    meta: [
      { title: "Annotation — MBSI Studio" },
      { name: "description", content: "Annotate regions and cell types on the tissue map." },
      { property: "og:title", content: "Annotation — MBSI Studio" },
      { property: "og:description", content: "Annotate regions and cell types on the tissue map." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <Workspace>
      <h1 className="mb-4 text-xl font-semibold">Annotation</h1>
      <div className="h-[60vh]">
        <EmptyState title="Nothing to show yet" body="Annotation tools are not yet supported by the backend." action={<UploadButton />} />
      </div>
    </Workspace>
  ),
});
