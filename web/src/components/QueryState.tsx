import type { UseQueryResult } from "@tanstack/react-query";
import type { ReactNode } from "react";

/** Renders loading and error states for a query, and `children` with its data once it has loaded. */
export default function QueryState<T>({
  query,
  children,
}: {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) {
    return (
      <div className="empty" role="status">
        Loading…
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="empty" role="alert">
        <p className="note">Couldn't load this: {query.error.message}</p>
        <button className="btn" onClick={() => void query.refetch()}>
          Retry
        </button>
      </div>
    );
  }
  return <>{children(query.data)}</>;
}
