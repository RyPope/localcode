"""Application status and content updates."""

import json
import sqlite3

from localcode import db
from localcode.importer import manager
from localcode.judging import runner_client
from localcode.services.errors import ServiceError
from localcode.services.models import AppStatus, ContentMeta, ImportStarted

_JSON_META = ("stats", "sources")


def _content_meta() -> ContentMeta:
    con = sqlite3.connect(f"{db.CONTENT_DB.as_uri()}?mode=ro", uri=True)
    try:
        meta = dict(con.execute("select key, value from meta").fetchall())
    finally:
        con.close()
    return {k: json.loads(v) if k in _JSON_META else v for k, v in meta.items()}  # type: ignore[return-value]


def status() -> AppStatus:
    imported = db.CONTENT_DB.exists()
    return {
        "imported": imported,
        "import": manager.snapshot(),
        "meta": _content_meta() if imported else {},
        "toolchains": runner_client.versions(),
    }


def start_import() -> ImportStarted:
    if not manager.start():
        raise ServiceError(409, "An import is already running")
    return {"started": True}
