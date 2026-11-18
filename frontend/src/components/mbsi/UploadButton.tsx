import { useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Plus, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Button, type ButtonProps } from "@/components/ui/button";
import { mbsi, type DatasetSummary, type DatasetUploadResponse } from "@/lib/mbsi-api";

export function UploadButton({
  label = "Upload dataset",
  variant = "default",
  className,
  sample = false,
  onUploaded,
}: {
  label?: string;
  variant?: ButtonProps["variant"];
  className?: string;
  sample?: boolean;
  onUploaded?: (dataset: DatasetUploadResponse) => void;
}) {
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const Icon = sample || label === "Add sample" ? Plus : Upload;

  return (
    <Button asChild variant={variant} size="sm" className={className} disabled={busy}>
      <label className={busy ? "cursor-wait" : "cursor-pointer"}>
        {busy ? <LoaderCircle className="animate-spin" /> : <Icon />}
        {busy ? "Uploading…" : label}
        <input
          ref={inputRef}
          type="file"
          className="sr-only"
          disabled={busy}
          onChange={async (event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            setBusy(true);
            try {
              const result = await mbsi.upload(file, {});
              queryClient.setQueryData<DatasetSummary[]>(
                ["uploaded-datasets"],
                (current = []) => [
                  ...current.filter((dataset) => dataset.dataset_id !== result.dataset_id),
                  {
                    dataset_id: result.dataset_id,
                    project_id: "",
                    sample_id: "",
                    platform: result.platform,
                    readiness: result.readiness,
                    summary: result.summary,
                    has_spatial_data: Boolean(result.adata_path),
                  },
                ],
              );
              queryClient.setQueryData(["last-upload"], result);
              onUploaded?.(result);
              await queryClient.invalidateQueries({ queryKey: ["uploaded-datasets"] });
              await queryClient.invalidateQueries({ queryKey: ["results"] });
              const ready = String(result.readiness?.status ?? "").toLowerCase() === "ready";
              if (ready) {
                toast.success("Dataset uploaded and ready", { description: file.name });
              } else {
                toast.warning("Dataset uploaded; readiness not confirmed", {
                  description: [file.name, ...result.warnings].join(" — ").slice(0, 300),
                });
              }
            } catch (error) {
              toast.error("Upload failed", { description: (error as Error).message });
            } finally {
              setBusy(false);
              if (inputRef.current) inputRef.current.value = "";
            }
          }}
        />
      </label>
    </Button>
  );
}
