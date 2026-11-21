import { act, renderHook } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { useMbsiConnection } from "@/hooks/use-mbsi-connection";
import { resetApiConnection, resolveApiUrl, saveApiConnection } from "@/lib/mbsi-connection";

afterEach(() => {
  sessionStorage.clear();
});

it("updates a mounted scientific-service subscriber when connection changes and resets", () => {
  saveApiConnection("https://first-scientific.example");
  const { result } = renderHook(() => useMbsiConnection());
  expect(result.current).toBe("https://first-scientific.example");
  act(() => saveApiConnection("https://second-scientific.example"));
  expect(result.current).toBe("https://second-scientific.example");
  act(() => resetApiConnection());
  expect(result.current).toBe(
    resolveApiUrl(
      import.meta.env["VITE_MBSI_API_URL"] as string | undefined,
      window.location.hostname,
    ),
  );
});
