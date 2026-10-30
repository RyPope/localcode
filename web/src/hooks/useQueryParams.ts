import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Page filters stored in the URL so views are linkable and survive reloads.
 * `set` merges a patch (empty string removes a key) and resets pagination unless `page` is in the patch.
 */
export function useQueryParams() {
  const [params, setParams] = useSearchParams();
  const get = useCallback((key: string, fallback = "") => params.get(key) ?? fallback, [params]);
  const set = useCallback(
    (patch: Record<string, string>) => {
      const next = new URLSearchParams(params);
      for (const [key, value] of Object.entries(patch)) {
        if (value) next.set(key, value);
        else next.delete(key);
      }
      if (!("page" in patch)) next.delete("page");
      setParams(next, { replace: true });
    },
    [params, setParams],
  );
  return { get, set };
}
