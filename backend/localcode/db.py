"""SQLite schemas and connections. content.db is rebuilt by imports; user.db never is."""
import sqlite3
from pathlib import Path

from localcode.config import CONTENT_DB, USER_DB

CONTENT_SCHEMA = """
create table if not exists problems(slug text primary key, frontend_id int, title text, difficulty text,
  tags text, acceptance real, description_html text, method text, params text, compare_mode text,
  examples text, ref_python text, has_tests int, langs text);
create table if not exists starters(slug text, lang text, code text, cpp_sig text, primary key(slug, lang));
create table if not exists solutions(slug text, idx int, title text, explanation_md text, code text,
  primary key(slug, idx));
create table if not exists tests(slug text primary key, cases text);
create table if not exists companies(slug text primary key, name text);
create table if not exists company_problems(company text, slug text, window text, frequency real,
  primary key(company, slug, window));
create index if not exists company_problems_slug on company_problems(slug);
create table if not exists meta(key text primary key, value text);
"""

USER_SCHEMA = """
create table if not exists drafts(slug text, lang text, code text, updated_at text, primary key(slug, lang));
create table if not exists submissions(id integer primary key, slug text, lang text, code text, verdict text,
  passed int, total int, runtime_ms real, memory_kb int, failing text, created_at text);
create index if not exists submissions_slug on submissions(slug);
create table if not exists settings(key text primary key, value text);
"""


def connect(path: Path, schema: str) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(schema)
    return con


def connect_content(path: Path | None = None) -> sqlite3.Connection:
    return connect(path or CONTENT_DB, CONTENT_SCHEMA)


def connect_user(path: Path | None = None) -> sqlite3.Connection:
    return connect(path or USER_DB, USER_SCHEMA)
