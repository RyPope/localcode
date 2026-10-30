import type { ProblemQuery, Window } from "../api";
import type { SegmentOption } from "../components/ui";

type DifficultyFilter = NonNullable<ProblemQuery["difficulty"]>;
type StatusFilter = NonNullable<ProblemQuery["status"]>;

export const WINDOWS: readonly Window[] = ["30d", "3m", "6m", "older", "all"];
export const DIFFICULTY_FILTERS: readonly DifficultyFilter[] = ["", "Easy", "Medium", "Hard"];
export const STATUS_FILTERS: readonly StatusFilter[] = ["", "solved", "attempted", "todo", "unsolved"];

export const DIFFICULTY_OPTIONS: readonly SegmentOption<DifficultyFilter>[] = DIFFICULTY_FILTERS.map((d) => ({
  value: d,
  label: d || "All",
}));

/** Narrow an untrusted string (e.g. from the URL) to one of `allowed`, else `fallback`. */
export function oneOf<T extends string>(value: string | null | undefined, allowed: readonly T[], fallback: T): T {
  return allowed.includes(value as T) ? (value as T) : fallback;
}
