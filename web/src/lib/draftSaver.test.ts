import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DraftSaver, type SaveState } from "./draftSaver";

type Call = { lang: string; code: string; keepalive: boolean };

function setup(save: (c: Call) => Promise<void>) {
  const states: SaveState[] = [];
  const calls: Call[] = [];
  const saver = new DraftSaver({
    delayMs: 800,
    retryMs: 3000,
    save: (lang, code, opts) => {
      const call = { lang, code, keepalive: !!opts?.keepalive };
      calls.push(call);
      return save(call);
    },
    onState: (s) => states.push(s),
  });
  return { saver, states, calls };
}

describe("DraftSaver", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("debounces and saves only the latest code", async () => {
    const { saver, calls, states } = setup(async () => {});
    saver.schedule("python", "a");
    saver.schedule("python", "ab");
    await vi.advanceTimersByTimeAsync(800);
    expect(calls).toEqual([{ lang: "python", code: "ab", keepalive: false }]);
    expect(states.at(-1)).toBe("saved");
  });

  it("keeps the edit and retries after a failed save", async () => {
    let fail = true;
    const { saver, calls, states } = setup(async () => {
      if (fail) throw new Error("offline");
    });
    saver.schedule("java", "x");
    await vi.advanceTimersByTimeAsync(800);
    expect(states.at(-1)).toBe("error");
    fail = false;
    await vi.advanceTimersByTimeAsync(3000);
    expect(calls.map((c) => c.code)).toEqual(["x", "x"]);
    expect(states.at(-1)).toBe("saved");
  });

  it("does not let a failed older save overwrite a newer edit", async () => {
    let reject!: (e: Error) => void;
    const { saver, calls } = setup((c) =>
      c.code === "old" ? new Promise((_, rej) => (reject = rej)) : Promise.resolve(),
    );
    saver.schedule("cpp", "old");
    await vi.advanceTimersByTimeAsync(800);
    saver.schedule("cpp", "new");
    reject(new Error("boom"));
    await vi.advanceTimersByTimeAsync(800);
    expect(calls.map((c) => c.code)).toEqual(["old", "new"]);
  });

  it("flushes pending edits with keepalive when the page is closing", () => {
    const { saver, calls } = setup(async () => {});
    saver.schedule("kotlin", "k");
    saver.flushOnExit();
    expect(calls).toEqual([{ lang: "kotlin", code: "k", keepalive: true }]);
  });

  it("flush saves immediately", async () => {
    const { saver, calls } = setup(async () => {});
    saver.schedule("python", "now");
    await saver.flush();
    expect(calls.map((c) => c.code)).toEqual(["now"]);
  });
});
