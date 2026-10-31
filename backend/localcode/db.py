"""SQLite schemas and connection sessions.

content.db is rebuilt from upstream sources on every import and swapped in atomically.
user.db holds drafts and submissions and is never touched by an import.
"""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from localcode.config import CONTENT_DB, USER_DB

CONTENT_SCHEMA = """
create table if not exists problems(slug text primary key, frontend_id int, title text, difficulty text,
  tags text, acceptance real, description_html text, method text, params text, ret text, compare_mode text,
  examples text, ref_python text, has_tests int, langs text, source text);
create table if not exists starters(slug text, lang text, code text, cpp_sig text, primary key(slug, lang));
create table if not exists solutions(slug text, idx int, title text, explanation_md text, code text, source text,
  primary key(slug, idx));
create table if not exists tests(slug text primary key, cases text);
create table if not exists companies(slug text primary key, name text);
create table if not exists company_problems(company text, slug text, window text, frequency real,
  primary key(company, slug, window));
create index if not exists company_problems_slug on company_problems(slug);
create table if not exists meta(key text primary key, value text);
"""

# user.db outlives every release, so its schema only changes through migrations.
# Append new entries; never edit or reorder existing ones. The index + 1 is the schema version
# recorded in PRAGMA user_version. Version 1 uses "if not exists" so pre-versioning databases adopt it.
USER_MIGRATIONS: list[str] = [
    """
    create table if not exists drafts(slug text, lang text, code text, updated_at text, primary key(slug, lang));
    create table if not exists submissions(id integer primary key, slug text, lang text, code text, verdict text,
      passed int, total int, runtime_ms real, memory_kb int, failing text, created_at text);
    create index if not exists submissions_slug on submissions(slug);
    create table if not exists settings(key text primary key, value text);
    """,
]

_migrated: set[Path] = set()
_migrate_lock = threading.Lock()


def migrate_user_db(path: Path | None = None) -> int:
    """Bring user.db up to the latest schema, one transaction per migration. Returns the version."""
    path = path or USER_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, isolation_level=None)
    try:
        current = con.execute("pragma user_version").fetchone()[0]
        if current > len(USER_MIGRATIONS):
            raise RuntimeError(
                f"{path} was written by a newer localcode (schema v{current}); upgrade localcode to open it"
            )
        for version, sql in enumerate(USER_MIGRATIONS[current:], start=current + 1):
            try:
                con.executescript(f"begin;\n{sql}\npragma user_version = {version};\ncommit;")
            except sqlite3.Error:
                if con.in_transaction:
                    con.execute("rollback")
                raise
        return len(USER_MIGRATIONS)
    finally:
        con.close()


def connect(path: Path, schema: str | None = None) -> sqlite3.Connection:
    """Open a connection (creating `schema` if given). Callers own closing it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    if schema:
        con.executescript(schema)
    return con


def connect_content(path: Path | None = None) -> sqlite3.Connection:
    """Writable content.db with its schema; used by the importer."""
    return connect(path or CONTENT_DB, CONTENT_SCHEMA)


def connect_user(path: Path | None = None) -> sqlite3.Connection:
    """user.db, migrated to the latest schema on first use in this process."""
    path = path or USER_DB
    if path not in _migrated:
        with _migrate_lock:
            if path not in _migrated:
                migrate_user_db(path)
                _migrated.add(path)
    return connect(path)


@contextmanager
def _session(con: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        with con:
            yield con
    finally:
        con.close()


def user_session() -> Iterator[sqlite3.Connection]:
    """Read/write access to user.db."""
    return _session(connect_user())


class ContentNotImported(Exception):
    """content.db does not exist yet (the first import has not finished)."""


@contextmanager
def content_session() -> Iterator[sqlite3.Connection]:
    """Read-only content.db with user.db attached as schema `u` (for per-user status in queries).

    Opened per call because imports replace content.db on disk. Never creates content.db:
    only the importer does, so its existence means an import completed.
    """
    if not CONTENT_DB.exists():
        raise ContentNotImported
    connect_user().close()  # make sure user.db and its schema exist before attaching
    con = sqlite3.connect(f"{CONTENT_DB.as_uri()}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("attach database ? as u", (str(USER_DB),))
    with _session(con) as c:
        yield c
