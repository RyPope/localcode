import { describe, expect, it } from "vitest";
import { problemLabel, refreshSummary } from "./labels";

describe("problemLabel", () => {
  it("prefixes the number when there is one", () =>
    expect(problemLabel({ id: 1, title: "Two Sum" })).toBe("1. Two Sum"));
  it("shows just the title for unnumbered problems", () =>
    expect(problemLabel({ id: null, title: "Count Vowels" })).toBe("Count Vowels"));
});

describe("refreshSummary", () => {
  it("lists totals, local content and what was kept", () =>
    expect(
      refreshSummary({
        problems: 4100,
        companies: 423,
        local_problems: 2,
        local_solutions: 5,
        kept_problems: 1,
        kept_solutions: 0,
        kept_cases: 12,
      }),
    ).toEqual([
      "4,100 problems",
      "423 companies",
      "2 local problems, 5 local solutions",
      "kept 1 problem, 12 test cases no longer in its source",
    ]));
  it("omits parts that are zero or missing (imports from older versions)", () =>
    expect(refreshSummary({ problems: 10, companies: 1 })).toEqual(["10 problems", "1 company"]));
});
