export type SaveState = "saved" | "saving" | "dirty" | "error";

type Save = (lang: string, code: string, opts?: { keepalive?: boolean }) => Promise<void>;

export interface DraftSaverOptions {
  save: Save;
  onState: (state: SaveState) => void;
  /** Debounce after the last keystroke. */
  delayMs: number;
  /** Wait before retrying a failed save. */
  retryMs: number;
}

/**
 * Debounced, retrying draft persistence. An edit is only forgotten once the server has
 * acknowledged it; a failed save is retried unless a newer edit has replaced it.
 */
export class DraftSaver {
  private pending: { lang: string; code: string } | null = null;
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor(private readonly opts: DraftSaverOptions) {}

  schedule(lang: string, code: string): void {
    this.pending = { lang, code };
    this.opts.onState("dirty");
    this.arm(this.opts.delayMs);
  }

  async flush(): Promise<void> {
    clearTimeout(this.timer);
    const edit = this.pending;
    if (!edit) return;
    this.pending = null;
    this.opts.onState("saving");
    try {
      await this.opts.save(edit.lang, edit.code);
      this.opts.onState(this.pending ? "dirty" : "saved");
    } catch {
      if (this.pending) return; // a newer edit is already scheduled and supersedes this one
      this.pending = edit;
      this.opts.onState("error");
      this.arm(this.opts.retryMs);
    }
  }

  /** Best-effort save while the page unloads (fetch keepalive outlives the document). */
  flushOnExit(): void {
    clearTimeout(this.timer);
    const edit = this.pending;
    if (!edit) return;
    this.pending = null;
    void this.opts.save(edit.lang, edit.code, { keepalive: true }).catch(() => {});
  }

  dispose(): void {
    clearTimeout(this.timer);
  }

  private arm(ms: number): void {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => void this.flush(), ms);
  }
}
