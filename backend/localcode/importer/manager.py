"""Runs fetch + build in a background thread and exposes progress for /api/status."""

import threading
import traceback

from localcode import config, db
from localcode.importer.build import build_content_db
from localcode.importer.fetch import fetch_all

STEPS = ["download", "problems", "solutions", "tests", "companies", "done"]
_lock = threading.Lock()
state = {"running": False, "step": None, "done": 0, "total": 0, "log": [], "error": None}


def _log(msg: str) -> None:
    state["log"] = (state["log"] + [msg])[-50:]


def _progress(step: str, done: int, total: int) -> None:
    state.update(step=step, done=done, total=total)


def _work() -> None:
    try:
        _progress("download", 0, 0)
        used = fetch_all(config.SOURCES_DIR, _log)
        _log("building database")
        stats = build_content_db(config.SOURCES_DIR, db.CONTENT_DB, _progress, used)
        _log(f"imported {stats['problems']} problems, {stats['with_tests']} with tests, {stats['companies']} companies")
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
