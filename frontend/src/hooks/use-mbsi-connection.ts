import { useSyncExternalStore } from "react";
import { getApiUrl, subscribeApiConnection } from "@/lib/mbsi-connection";

// Stable SSR snapshot; the scientific-service preference is read after subscription.
export function useMbsiConnection() {
  return useSyncExternalStore(subscribeApiConnection, getApiUrl, () => "");
}
