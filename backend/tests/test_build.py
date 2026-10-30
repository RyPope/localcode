import json
import shutil
import sqlite3
from pathlib import Path

from localcode import db
from localcode.importer.build import build_content_db

FIX = Path(__file__).parent / "fixtures"


def make_src(tmp_path: Path) -> Path:
    src = tmp_path / "sources"
    (src / "dataset").mkdir(parents=True)
    shutil.copy(FIX / "dataset_rows.jsonl", src / "dataset" / "LeetCodeDataset-train.jsonl")
    shutil.copytree(FIX / "doocs", src / "doocs")
    shutil.copytree(FIX / "companies", src / "companies")
    return src


def test_build_from_fixtures(tmp_path):
    out = tmp_path / "content.db"
    steps = []
    build_content_db(make_src(tmp_path), out, progress=lambda step, done, total: steps.append(step))
    con = sqlite3.connect(out)
    con.row_factory = sqlite3.Row
    assert con.execute("select count(*) from problems").fetchone()[0] == 4
    p = con.execute("select * from problems where slug='pair-sum'").fetchone()
    assert p["title"] == "Pair Sum" and p["frontend_id"] == 7
    assert json.loads(p["langs"]) == ["python", "java", "cpp", "kotlin"]
    assert p["has_tests"] == 1 and p["acceptance"] == 0.55
    assert "<code>goal</code>" in p["description_html"]
    fill = con.execute("select * from problems where slug='fill-in-place'").fetchone()
    assert fill["has_tests"] == 0 and fill["title"] == "Fill In Place"
    assert fill["description_html"].startswith("<pre")
    starters = {r["lang"]: r for r in con.execute("select * from starters where slug='pair-sum'")}
    assert set(starters) == {"python", "java", "cpp", "kotlin"}
    assert json.loads(starters["cpp"]["cpp_sig"])["method"] == "pairSum"
    assert con.execute("select count(*) from solutions where slug='pair-sum'").fetchone()[0] == 2
    assert len(json.loads(con.execute("select cases from tests where slug='pair-sum'").fetchone()[0])) == 4
    assert con.execute("select count(*) from companies").fetchone()[0] == 2
    assert con.execute("select frequency from company_problems where company='acme' and slug='pair-sum' and window='30d'").fetchone()[0] == 100.0
    assert "problems" in steps and "companies" in steps


def test_tree_problem_without_doocs_is_python_only(tmp_path):
    out = tmp_path / "content.db"
    build_content_db(make_src(tmp_path), out, progress=lambda *a: None)
    con = sqlite3.connect(out)
    assert json.loads(con.execute("select langs from problems where slug='tree-mirror'").fetchone()[0]) == ["python"]


def test_reimport_preserves_user_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "USER_DB", tmp_path / "user.db")
    monkeypatch.setattr(db, "CONTENT_DB", tmp_path / "content.db")
    with db.connect_user() as u:
        u.execute("insert into drafts values ('pair-sum', 'python', 'x = 1', '2026-10-30')")
    src = make_src(tmp_path)
    build_content_db(src, tmp_path / "content.db", progress=lambda *a: None)
    build_content_db(src, tmp_path / "content.db", progress=lambda *a: None)
    with db.connect_user() as u:
        assert u.execute("select code from drafts").fetchone()[0] == "x = 1"
    with db.connect_content() as c:
        assert c.execute("select count(*) from problems").fetchone()[0] == 4
