import sqlite3

import pytest

from localcode import db


def version(path):
    return sqlite3.connect(path).execute("pragma user_version").fetchone()[0]


def test_fresh_user_db_is_at_latest_version(tmp_path):
    db.migrate_user_db(tmp_path / "u.db")
    assert version(tmp_path / "u.db") == len(db.USER_MIGRATIONS)
    tables = {
        r[0] for r in sqlite3.connect(tmp_path / "u.db").execute("select name from sqlite_master where type='table'")
    }
    assert {"drafts", "submissions", "settings"} <= tables


def test_pre_versioning_db_keeps_its_data(tmp_path):
    path = tmp_path / "u.db"
    con = sqlite3.connect(path)
    con.executescript(
        "create table drafts(slug text, lang text, code text, updated_at text, primary key(slug, lang));"
        "insert into drafts values ('two-sum', 'python', 'x = 1', 't');"
    )
    con.close()
    db.migrate_user_db(path)
    assert version(path) == len(db.USER_MIGRATIONS)
    assert sqlite3.connect(path).execute("select code from drafts").fetchone()[0] == "x = 1"


def test_pending_migrations_apply_in_order_once(tmp_path, monkeypatch):
    path = tmp_path / "u.db"
    db.migrate_user_db(path)
    monkeypatch.setattr(
        db, "USER_MIGRATIONS", [*db.USER_MIGRATIONS, "alter table drafts add column pinned int default 0;"]
    )
    db.migrate_user_db(path)
    db.migrate_user_db(path)  # idempotent
    cols = [r[1] for r in sqlite3.connect(path).execute("pragma table_info(drafts)")]
    assert cols.count("pinned") == 1
    assert version(path) == len(db.USER_MIGRATIONS)


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    path = tmp_path / "u.db"
    db.migrate_user_db(path)
    before = version(path)
    monkeypatch.setattr(db, "USER_MIGRATIONS", [*db.USER_MIGRATIONS, "create table t(x int); this is not sql;"])
    with pytest.raises(sqlite3.Error):
        db.migrate_user_db(path)
    assert version(path) == before
    assert "t" not in {r[0] for r in sqlite3.connect(path).execute("select name from sqlite_master")}


def test_newer_user_db_is_refused(tmp_path):
    path = tmp_path / "u.db"
    sqlite3.connect(path).execute(f"pragma user_version = {len(db.USER_MIGRATIONS) + 1}")
    with pytest.raises(RuntimeError, match="newer"):
        db.migrate_user_db(path)
