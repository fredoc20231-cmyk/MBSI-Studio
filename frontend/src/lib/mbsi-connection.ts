// Connection preferences are tab-scoped; datasets and credentials are never stored here.
const CONNECTION_KEY = "mbsi-api-connection";
const CONNECTION_EVENT = "mbsi-api-connection-changed";
// Public deployed scientific service, retained in hosted builds without Vite environment settings.
export const DEFAULT_MBSI_API_URL = "https://mbsi-studio.onrender.com";

export function subscribeApiConnection(listener: () => void): () => void {
  window.addEventListener(CONNECTION_EVENT, listener);
  return () => window.removeEventListener(CONNECTION_EVENT, listener);
}

export function normalizeApiUrl(value: string, frontendProtocol = "https:"): string {
  const url = new URL(value.trim());
  if (url.username || url.password || url.search || url.hash) {
    throw new Error("Enter a service address without credentials, a query or a fragment.");
  }
  if (url.protocol !== "https:" && !(url.protocol === "http:" && frontendProtocol === "http:")) {
    throw new Error("Use an HTTPS service address for this app.");
  }
  // Users often copy the docs/health address rather than the service root.
  url.pathname = url.pathname.replace(/\/(?:docs|openapi\.json|api\/health|health)\/?$/, "");
  return url.toString().replace(/\/+$/, "");
}

export function resolveApiUrl(configured: string | undefined, hostname?: string): string {
  if (configured?.trim()) return configured.trim().replace(/\/+$/, "");
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]"
    ? "http://localhost:8000"
    : DEFAULT_MBSI_API_URL;
}

export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    try {
      const stored = window.sessionStorage.getItem(CONNECTION_KEY);
      if (stored) return normalizeApiUrl(stored, window.location.protocol);
    } catch {
      // A blocked storage preference must not prevent the configured connection.
    }
  }
  return resolveApiUrl(
    import.meta.env["VITE_MBSI_API_URL"] as string | undefined,
    typeof window !== "undefined" ? window.location.hostname : undefined,
  );
}

export function saveApiConnection(value: string): void {
  window.sessionStorage.setItem(CONNECTION_KEY, normalizeApiUrl(value, window.location.protocol));
  window.dispatchEvent(new Event(CONNECTION_EVENT));
}

export function resetApiConnection(): void {
  window.sessionStorage.removeItem(CONNECTION_KEY);
  window.dispatchEvent(new Event(CONNECTION_EVENT));
}

export function isMbsiHealth(value: unknown): value is {
  status: "healthy";
  version: string;
  milestone_1_platforms: string[];
} {
  if (!value || typeof value !== "object") return false;
  const health = value as Record<string, unknown>;
  return (
    health["status"] === "healthy" &&
    typeof health["version"] === "string" &&
    Array.isArray(health["milestone_1_platforms"]) &&
    health["milestone_1_platforms"].every((platform) => typeof platform === "string")
  );
}
