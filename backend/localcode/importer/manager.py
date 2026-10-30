"""Runs fetch + build in a background thread and exposes progress for /api/status."""

import threading
import traceback

from localcode.importer.pipeline import run_import

_lock = threading.Lock()
state = {"running": False, "step": None, "done": 0, "total": 0, "log": [], "error": None}


def _log(msg: str) -> None:
    state["log"] = (state["log"] + [msg])[-50:]


def _progress(step: str, done: int, total: int) -> None:
    state.update(step=step, done=done, total=total)


def _work() -> None:
    try:
        run_import(_log, _progress)
    except Exception as e:  # surfaced on the setup screen
        state["error"] = f"{type(e).__name__}: {e}"
        _log(traceback.format_exc(limit=3))
    finally:
        state["running"] = False


def snapshot() -> dict:
    return {**state, "log": list(state["log"])}


def start() -> bool:
    with _lock:
        if state["running"]:
            return False
        state.update(running=True, step="download", done=0, total=0, error=None, log=[])
        threading.Thread(target=_work, daemon=True).start()
        return True
