import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { api } from "../api";

const POLL_MS = 1500;

/**
 * App status, polled while the first import or an update is running. When an import finishes,
 * every cached query is invalidated so pages show the new content without a reload.
 */
export function useAppStatus() {
  const qc = useQueryClient();
  const status = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: (q) => (!q.state.data?.imported || q.state.data.import.running ? POLL_MS : false),
  });
  const wasRunning = useRef(false);
  const running = status.data?.import.running ?? false;
  useEffect(() => {
    if (wasRunning.current && !running) void qc.invalidateQueries();
    wasRunning.current = running;
  }, [running, qc]);
  return status;
}
