import { createFileRoute } from "@tanstack/react-router";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/integrate")({
  head: () => ({
    meta: [
      { title: "Integrate — MBSI Studio" },
      { name: "description", content: "Integrate Visium, Visium HD and Xenium datasets." },
      { property: "og:title", content: "Integrate — MBSI Studio" },
      { property: "og:description", content: "Integrate Visium, Visium HD and Xenium datasets." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <Workspace>
      <h1 className="mb-4 text-xl font-semibold">Integrate</h1>
      <div className="h-[60vh]">
        <EmptyState title="Nothing to show yet" body="Integration is unavailable until datasets are uploaded and analysed." action={<UploadButton />} />
      </div>
    </Workspace>
  ),
});
