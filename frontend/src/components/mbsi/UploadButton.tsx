import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { mbsi } from "@/lib/mbsi-api";

export function UploadButton() {
  const [busy, setBusy] = useState(false);
  return (
    <Button asChild disabled={busy}>
      <label className="cursor-pointer">
        {busy ? "Uploading…" : "Upload dataset"}
        <input
          type="file"
          className="sr-only"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setBusy(true);
            try {
              await mbsi.upload(f, {});
              toast.success("Dataset uploaded");
            } catch (err) {
              toast.error(`Upload failed: ${(err as Error).message}`);
            } finally {
              setBusy(false);
            }
          }}
        />
      </label>
    </Button>
  );
}
