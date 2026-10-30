import { describe, expect, it } from "vitest";
import { ApiError } from "../api";
import { shouldRetry } from "./retry";

describe("shouldRetry", () => {
  it("never retries client errors", () => {
    expect(shouldRetry(0, new ApiError("Unknown company", 404))).toBe(false);
    expect(shouldRetry(0, new ApiError("Bad input", 400))).toBe(false);
  });
  it("retries server and network errors a couple of times", () => {
    expect(shouldRetry(0, new ApiError("Runner unavailable", 503))).toBe(true);
    expect(shouldRetry(1, new TypeError("Failed to fetch"))).toBe(true);
    expect(shouldRetry(2, new TypeError("Failed to fetch"))).toBe(false);
  });
});
