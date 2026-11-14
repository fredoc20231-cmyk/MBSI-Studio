import { createFileRoute } from "@tanstack/react-router";
import { Workspace, EmptyState } from "@/components/mbsi/Workspace";
import { UploadButton } from "@/components/mbsi/UploadButton";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare — MBSI Studio" },
      { name: "description", content: "Compare samples and conditions side by side." },
      { property: "og:title", content: "Compare — MBSI Studio" },
      { property: "og:description", content: "Compare samples and conditions side by side." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <Workspace>
      <h1 className="mb-4 text-xl font-semibold">Compare</h1>
      <div className="h-[60vh]">
        <EmptyState title="Nothing to show yet" body="Comparison needs at least two analysed samples." action={<UploadButton />} />
      </div>
    </Workspace>
  ),
});
