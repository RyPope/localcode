import { ApiError } from "../api";

const MAX_RETRIES = 2;

/** Query retry policy: client errors (4xx) are final; server and network errors get a couple of retries. */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false;
  return failureCount < MAX_RETRIES;
}
