import { useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Plus, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Button, type ButtonProps } from "@/components/ui/button";
import { mbsi, type DatasetUploadResponse } from "@/lib/mbsi-api";

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
          multiple
          className="sr-only"
          disabled={busy}
          onChange={async (event) => {
            const files = Array.from(event.target.files ?? []);
            if (!files.length) return;
            setBusy(true);
            const uploaded: DatasetUploadResponse[] = [];
            const failed: { name: string; reason: string }[] = [];
            for (const file of files) {
              try {
                const result = await mbsi.upload(file, {});
                uploaded.push(result);
                queryClient.setQueryData<DatasetUploadResponse[]>(
                  ["uploaded-datasets"],
                  (current = []) => [
                    ...current.filter((dataset) => dataset.dataset_id !== result.dataset_id),
                    result,
                  ],
                );
                queryClient.setQueryData(["last-upload"], result);
                onUploaded?.(result);
              } catch (error) {
                failed.push({
                  name: file.name,
                  reason: error instanceof Error ? error.message : "Upload failed.",
                });
              }
            }
            setBusy(false);
            if (inputRef.current) inputRef.current.value = "";
            if (uploaded.length) {
              await queryClient.invalidateQueries({
                predicate: (query) => query.queryKey[0] !== "uploaded-datasets",
              });
              toast.success(
                uploaded.length === 1 ? "Dataset uploaded" : `${uploaded.length} datasets uploaded`,
                {
                  description:
                    uploaded.length === 1
                      ? "One dataset was accepted by the scientific backend."
                      : failed.length
                        ? `${failed.length} file(s) were not accepted: ${failed.map((file) => `${file.name}: ${file.reason}`).join("; ")}`
                        : "All files were accepted by the scientific backend.",
                },
              );
            }
            if (failed.length && !uploaded.length) {
              toast.error("Upload failed", {
                description: failed.map((file) => `${file.name}: ${file.reason}`).join("; "),
              });
            }
          }}
        />
      </label>
    </Button>
  );
}
