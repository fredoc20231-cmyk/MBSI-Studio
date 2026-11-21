import { useEffect, useState } from "react";
import { Download, FileArchive, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { mbsi } from "@/lib/mbsi-api";
import type { LoupeArtifact as Artifact } from "@/lib/loupe";

export function LoupeArtifact({ artifact, service }: { artifact: Artifact; service: string }) {
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let objectUrl = "";
    setPreview("");
    setError("");
    if (artifact.kind === "image" && ["image/png", "image/svg+xml"].includes(artifact.mime_type)) {
      void mbsi.loupe
        .download(artifact.id, service)
        .then((blob) => {
          if (cancelled) return;
          objectUrl = URL.createObjectURL(new Blob([blob], { type: artifact.mime_type }));
          setPreview(objectUrl);
        })
        .catch((e: unknown) => {
          if (!cancelled) setError(e instanceof Error ? e.message : "Image unavailable.");
        });
    }
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [artifact.id, artifact.kind, artifact.mime_type, service]);

  async function download() {
    setBusy(true);
    setError("");
    try {
      const blob = await mbsi.loupe.download(artifact.id, service);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = artifact.name.replace(/[\\/]/g, "_");
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download unavailable.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="min-w-0 rounded-lg border border-border bg-card p-3">
      {preview && (
        <img
          src={preview}
          alt={artifact.name}
          className="mb-3 aspect-[4/3] w-full object-contain"
          onError={() => setError("The returned image could not be displayed.")}
        />
      )}
      <div className="flex items-center gap-2">
        {artifact.kind === "image" ? (
          <ImageIcon className="size-4 shrink-0 text-primary" />
        ) : (
          <FileArchive className="size-4 shrink-0 text-primary" />
        )}
        <div className="min-w-0 flex-1">
          <p className="break-all text-xs font-medium">{artifact.name}</p>
          <p className="text-[11px] text-muted-foreground">
            {artifact.kind} · Returned by scientific service
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          title="Download artifact"
          aria-label={`Download ${artifact.name}`}
          onClick={download}
          disabled={busy}
        >
          <Download />
        </Button>
      </div>
      {error && (
        <p role="alert" className="mt-2 break-words text-xs text-destructive">
          {error}
        </p>
      )}
    </article>
  );
}
