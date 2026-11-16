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
          className="sr-only"
          disabled={busy}
          onChange={async (event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            setBusy(true);
            try {
              const result = await mbsi.upload(file, {});
              queryClient.setQueryData<DatasetUploadResponse[]>(
                ["uploaded-datasets"],
                (current = []) => [
                  ...current.filter((dataset) => dataset.dataset_id !== result.dataset_id),
                  result,
                ],
              );
              queryClient.setQueryData(["last-upload"], result);
              onUploaded?.(result);
              await queryClient.invalidateQueries({
                predicate: (query) => query.queryKey[0] !== "uploaded-datasets",
              });
              toast.success("Dataset uploaded", {
                description: `${file.name} was accepted by the scientific backend.`,
              });
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
