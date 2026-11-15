import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Cable, Check, LoaderCircle, RotateCcw } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { checkMbsiConnection, getApiUrl, mbsi } from "@/lib/mbsi-api";
import { normalizeApiUrl, resetApiConnection, saveApiConnection } from "@/lib/mbsi-connection";

export function BackendConnection() {
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [connectedAddress, setConnectedAddress] = useState("");
  const health = useQuery({
    queryKey: ["health"],
    queryFn: mbsi.health,
    retry: false,
    refetchInterval: 30000,
  });
  const label = health.isPending
    ? "Checking scientific backend"
    : health.isSuccess
      ? "Scientific backend connected"
      : "Connect scientific backend";

  async function connect(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setConnectedAddress("");
    try {
      const url = normalizeApiUrl(address, window.location.protocol);
      const result = await checkMbsiConnection(url);
      const changed = url !== getApiUrl();
      await client.cancelQueries();
      saveApiConnection(url);
      // Identifiers from one scientific service must never be sent to another.
      if (changed) client.clear();
      client.setQueryData(["health"], result);
      setAddress(url);
      setConnectedAddress(url);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Connection failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (value) {
          setAddress(getApiUrl());
          setError("");
          setConnectedAddress("");
        }
      }}
    >
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Scientific backend"
          title={label}
          className="gap-2 text-xs text-muted-foreground"
        >
          <Cable />
          <span
            aria-hidden
            className={`h-2 w-2 rounded-full ${health.isSuccess ? "bg-success" : health.isPending ? "bg-warning" : "bg-destructive"}`}
          />
          <span className="hidden 2xl:inline">{label}</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90dvh] w-[calc(100%-2rem)] overflow-y-auto rounded-lg">
        <DialogHeader>
          <DialogTitle>Scientific backend</DialogTitle>
          <DialogDescription>MBSI Studio · existing repository service</DialogDescription>
        </DialogHeader>
        <form onSubmit={connect} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="mbsi-service-url" className="text-sm font-medium">
              Service address
            </label>
            <Input
              id="mbsi-service-url"
              type="url"
              required
              autoComplete="off"
              value={address}
              onChange={(event) => {
                setAddress(event.target.value);
                setConnectedAddress("");
              }}
              aria-describedby="mbsi-service-note"
            />
            <p
              id="mbsi-service-note"
              className="break-words text-xs leading-5 text-muted-foreground"
            >
              {getApiUrl()
                ? `Current address: ${getApiUrl()}`
                : "No deployed scientific service configured."}
            </p>
          </div>
          {error && (
            <p role="alert" className="break-words text-sm text-destructive">
              {error}
            </p>
          )}
          {connectedAddress && (
            <p role="status" className="flex items-start gap-2 break-all text-sm text-success">
              <Check className="mt-0.5 h-4 w-4 shrink-0" />
              Connected to {connectedAddress}
            </p>
          )}
          <div className="flex flex-wrap justify-between gap-2">
            <Button
              variant="outline"
              type="button"
              disabled={busy}
              onClick={async () => {
                await client.cancelQueries();
                resetApiConnection();
                client.clear();
                setAddress(getApiUrl());
                setError("");
                setConnectedAddress("");
              }}
            >
              <RotateCcw />
              Reset
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? <LoaderCircle className="animate-spin" /> : <Cable />}
              {busy ? "Checking…" : "Check & connect"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
