import { describe, expect, it } from "vitest";
import { oneOf, WINDOWS } from "./filters";

describe("oneOf", () => {
  it("keeps allowed values", () => expect(oneOf("3m", WINDOWS, "6m")).toBe("3m"));
  it("falls back for unknown or missing values", () => {
    expect(oneOf("1y", WINDOWS, "6m")).toBe("6m");
    expect(oneOf(null, WINDOWS, "6m")).toBe("6m");
  });
});
