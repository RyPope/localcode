import json
import shutil
import sqlite3
from pathlib import Path

import pytest

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
    assert p["ret"] == "List[int]"
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
    assert (
        con.execute(
            "select frequency from company_problems where company='acme' and slug='pair-sum' and window='30d'"
        ).fetchone()[0]
        == 100.0
    )
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


def test_build_filters_invalid_cases_and_applies_exclusions(tmp_path):
    from localcode.importer.case_filter import case_key

    src = make_src(tmp_path)
    rows = [json.loads(line) for line in (src / "dataset" / "LeetCodeDataset-train.jsonl").read_text().splitlines()]
    rows[0]["test"] += (
        "    assert candidate(nums = [1, 2],goal = 4294967296) == [0, 1]\n    assert candidate(nums = [1],goal = 7) == None\n"
    )
    (src / "dataset" / "LeetCodeDataset-train.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "content.db"
    build_content_db(src, out, progress=lambda *a: None, excluded={"pair-sum": {case_key([[0, 1], 1])}})
    cases = json.loads(sqlite3.connect(out).execute("select cases from tests where slug='pair-sum'").fetchone()[0])
    assert [c["args"] for c in cases] == [[[1, 4, 6], 10], [[5, 5], 10], [[2, 8, 3], 5]]


def test_failed_build_leaves_previous_db_and_no_temp_file(tmp_path, monkeypatch):
    from localcode.importer import build as build_module

    src = make_src(tmp_path)
    out = tmp_path / "content.db"
    build_content_db(src, out, progress=lambda *a: None)
    before = out.read_bytes()

    def boom(*args, **kwargs):
        raise RuntimeError("corrupt source")

    monkeypatch.setattr(build_module, "_problem_rows", boom)
    with pytest.raises(RuntimeError):
        build_content_db(src, out, progress=lambda *a: None)
    assert out.read_bytes() == before
    assert not out.with_suffix(".tmp").exists()


CONTENT = FIX / "content"


def build_with_content(tmp_path: Path, content: Path = CONTENT) -> tuple[sqlite3.Connection, dict]:
    out = tmp_path / "content.db"
    stats = build_content_db(make_src(tmp_path), out, progress=lambda *a: None, content_dir=content)
    con = sqlite3.connect(out)
    con.row_factory = sqlite3.Row
    return con, stats


def write_content(root: Path, slug: str, files: dict[str, str]) -> Path:
    for name, text in files.items():
        f = root / "problems" / slug / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    return root


def test_local_new_problem_is_runnable(tmp_path):
    con, stats = build_with_content(tmp_path)
    p = con.execute("select * from problems where slug='count-vowels'").fetchone()
    assert p["source"] == "local" and p["frontend_id"] is None and p["title"] == "Count Vowels"
    assert p["method"] == "countVowels" and json.loads(p["params"]) == [{"name": "s", "type": "str"}]
    assert p["ret"] == "int" and p["has_tests"] == 1 and p["compare_mode"] == "exact"
    assert p["ref_python"].startswith("class Solution:")
    assert json.loads(p["langs"]) == ["python", "java", "kotlin"]
    starters = {r["lang"]: r["code"] for r in con.execute("select * from starters where slug='count-vowels'")}
    assert "def countVowels(self, s: str) -> int:" in starters["python"]
    assert "return sum" not in starters["python"]
    [sol] = con.execute("select * from solutions where slug='count-vowels'").fetchall()
    assert sol["source"] == "local" and sol["title"] == "Single scan"
    assert stats["local_problems"] == 1 and stats["local_solutions"] == 2


def test_overlay_appends_solution_and_enables_language(tmp_path):
    content = write_content(
        tmp_path / "c",
        "tree-mirror",
        {
            "solutions/01-recursive.md": "---\ntitle: Recursive\n---\nSwap children.\n\n```java\n"
            "class Solution {\n    public TreeNode mirror(TreeNode root) {\n        return root;\n    }\n}\n```\n"
        },
    )
    con, _ = build_with_content(tmp_path, content)
    p = con.execute("select * from problems where slug='tree-mirror'").fetchone()
    assert p["source"] == "upstream" and p["title"] == "Tree Mirror"
    assert json.loads(p["langs"]) == ["python", "java", "kotlin"]
    sols = con.execute("select title, source from solutions where slug='tree-mirror' order by idx").fetchall()
    assert [tuple(s) for s in sols] == [("Recursive", "local")]


def test_overlay_solution_with_wrong_signature_adds_no_language(tmp_path):
    content = write_content(
        tmp_path / "c",
        "tree-mirror",
        {
            "solutions/01.md": "---\ntitle: Odd\n---\n```java\nclass Solution {\n    public int other(int x) {\n"
            "        return x;\n    }\n}\n```\n"
        },
    )
    con, _ = build_with_content(tmp_path, content)
    assert json.loads(con.execute("select langs from problems where slug='tree-mirror'").fetchone()[0]) == ["python"]


def test_overlay_overrides_metadata_and_cases(tmp_path):
    content = write_content(
        tmp_path / "c",
        "pair-sum",
        {
            "problem.md": "---\ndifficulty: Hard\ntags: [Array]\n---\nA *new* statement.\n",
            "tests.json": json.dumps(
                [{"args": [[0, 1], 1], "expected": [1, 0]}, {"args": [[3, 4], 7], "expected": [0, 1]}]
            ),
        },
    )
    con, _ = build_with_content(tmp_path, content)
    p = con.execute("select * from problems where slug='pair-sum'").fetchone()
    assert p["difficulty"] == "Hard" and json.loads(p["tags"]) == ["Array"] and p["title"] == "Pair Sum"
    assert p["description_html"] == "<p>A <em>new</em> statement.</p>"
    cases = json.loads(con.execute("select cases from tests where slug='pair-sum'").fetchone()[0])
    by_args = {json.dumps(c["args"]): c["expected"] for c in cases}
    assert len(cases) == 5 and by_args["[[0, 1], 1]"] == [1, 0] and by_args["[[3, 4], 7]"] == [0, 1]


def test_overlay_makes_untested_upstream_problem_runnable(tmp_path):
    content = write_content(
        tmp_path / "c",
        "fill-in-place",
        {
            "tests.json": json.dumps([{"args": [[n]], "expected": n * 2} for n in range(3)]),
            "solutions/01.md": "---\ntitle: Double\n---\n```python\nclass Solution:\n"
            "    def double(self, nums: List[int]) -> int:\n        return nums[0] * 2\n```\n",
        },
    )
    con, _ = build_with_content(tmp_path, content)
    p = con.execute("select * from problems where slug='fill-in-place'").fetchone()
    assert p["has_tests"] == 1 and p["method"] == "double" and p["source"] == "local"
    assert p["title"] == "Fill In Place"


def test_skipped_folder_reported_in_stats(tmp_path):
    _, stats = build_with_content(tmp_path)
    [entry] = stats["skipped"]
    assert entry["path"].endswith("broken/problem.md") and "difficulty" in entry["reason"]


def drop_dataset_row(src: Path, slug: str) -> None:
    f = src / "dataset" / "LeetCodeDataset-train.jsonl"
    f.write_text("".join(line for line in f.read_text().splitlines(True) if json.loads(line)["task_id"] != slug))


def rebuild(tmp_path: Path, content: Path | None = None, mutate=None) -> tuple[sqlite3.Connection, dict]:
    """Build again into the same content.db from freshly copied sources, after `mutate(src)`."""
    work = tmp_path / f"run-{len(list(tmp_path.glob('run-*')))}"
    src = make_src(work)
    if mutate:
        mutate(src)
    out = tmp_path / "content.db"
    stats = build_content_db(src, out, progress=lambda *a: None, content_dir=content)
    con = sqlite3.connect(out)
    con.row_factory = sqlite3.Row
    return con, stats


EXTRA = {
    "solutions/01-extra.md": "---\ntitle: Extra\n---\n```python\nclass Solution:\n"
    "    def pairSum(self, nums: List[int], goal: int) -> List[int]:\n        return []\n```\n",
    "tests.json": json.dumps([{"args": [[3, 4], 7], "expected": [0, 1]}]),
}


def test_second_import_keeps_removed_problem_solution_and_case(tmp_path):
    first = write_content(tmp_path / "c1", "pair-sum", EXTRA)
    rebuild(tmp_path, first)
    con, stats = rebuild(tmp_path, tmp_path / "empty", mutate=lambda src: drop_dataset_row(src, "list-reverse"))
    lr = con.execute("select * from problems where slug='list-reverse'").fetchone()
    assert lr is not None and lr["has_tests"] == 1 and lr["method"] == "rev"
    assert con.execute("select count(*) from starters where slug='list-reverse'").fetchone()[0] >= 1
    titles = [r[0] for r in con.execute("select title from solutions where slug='pair-sum' order by idx")]
    assert titles == ["Hash Map", "Solution 2", "Extra"]
    cases = json.loads(con.execute("select cases from tests where slug='pair-sum'").fetchone()[0])
    assert [[3, 4], 7] in [c["args"] for c in cases]
    assert stats["kept_problems"] == 1 and stats["kept_solutions"] == 1 and stats["kept_cases"] == 1


def test_second_import_is_stable(tmp_path):
    rebuild(tmp_path, CONTENT)
    con, stats = rebuild(tmp_path, CONTENT)
    assert stats["kept_problems"] == stats["kept_solutions"] == stats["kept_cases"] == 0
    assert con.execute("select count(*) from solutions where slug='count-vowels'").fetchone()[0] == 1


def test_kept_cases_filtered_by_new_signature(tmp_path):
    rebuild(tmp_path, CONTENT)
    changed = write_content(
        tmp_path / "c2",
        "count-vowels",
        {
            "tests.json": json.dumps(
                [{"args": ["ab", "a"], "expected": 1} for _ in range(1)]
                + [{"args": ["x", "y"], "expected": 0}, {"args": ["aa", "a"], "expected": 2}]
            ),
            "solutions/01-scan.md": "---\ntitle: Single scan\n---\n```python\nclass Solution:\n"
            "    def countVowels(self, s: str, vowels: str) -> int:\n        return sum(c in vowels for c in s)\n```\n",
        },
    )
    con, stats = rebuild(tmp_path, changed)
    cases = json.loads(con.execute("select cases from tests where slug='count-vowels'").fetchone()[0])
    assert len(cases) == 3 and all(len(c["args"]) == 2 for c in cases)
    assert stats["kept_cases"] == 0
    assert con.execute("select count(*) from solutions where slug='count-vowels'").fetchone()[0] == 1


def test_carry_forward_never_overrides_local_case(tmp_path):
    rebuild(tmp_path)
    override = write_content(
        tmp_path / "c", "pair-sum", {"tests.json": json.dumps([{"args": [[0, 1], 1], "expected": [9, 9]}])}
    )
    con, _ = rebuild(tmp_path, override)
    cases = json.loads(con.execute("select cases from tests where slug='pair-sum'").fetchone()[0])
    assert [c["expected"] for c in cases if c["args"] == [[0, 1], 1]] == [[9, 9]]


def test_local_problem_keeps_control_when_upstream_adds_it(tmp_path):
    local = write_content(
        tmp_path / "c",
        "list-reverse",
        {
            "tests.json": json.dumps([{"args": [n], "expected": n} for n in range(3)]),
            "solutions/01.md": "---\ntitle: Mine\n---\n```python\nclass Solution:\n"
            "    def same(self, n: int) -> int:\n        return n\n```\n",
        },
    )
    rebuild(tmp_path, local, mutate=lambda src: drop_dataset_row(src, "list-reverse"))
    con, _ = rebuild(tmp_path, local)
    p = con.execute("select * from problems where slug='list-reverse'").fetchone()
    assert p["source"] == "local" and p["method"] == "same" and p["has_tests"] == 1


def test_carry_forward_from_db_without_source_column(tmp_path):
    rebuild(tmp_path)
    old = sqlite3.connect(tmp_path / "content.db")
    old.execute("alter table problems drop column source")
    old.execute("alter table solutions drop column source")
    old.commit()
    old.close()
    con, stats = rebuild(tmp_path, mutate=lambda src: drop_dataset_row(src, "tree-mirror"))
    assert con.execute("select source from problems where slug='tree-mirror'").fetchone()[0] == "upstream"
    assert stats["kept_problems"] == 1


def _int_problem(root: Path, typ: str, ret: str, cases: list) -> Path:
    return write_content(
        root,
        "typed",
        {
            "tests.json": json.dumps(cases),
            "solutions/01.md": f"---\ntitle: A\n---\n```python\nclass Solution:\n"
            f"    def f(self, a: {typ}) -> {ret}:\n        return a\n```\n",
        },
    )


def test_type_change_drops_carried_cases(tmp_path):
    rebuild(tmp_path, _int_problem(tmp_path / "c1", "int", "int", [{"args": [n], "expected": n} for n in range(3)]))
    strs = [{"args": [s], "expected": s} for s in "abc"]
    con, stats = rebuild(tmp_path, _int_problem(tmp_path / "c2", "str", "str", strs))
    cases = json.loads(con.execute("select cases from tests where slug='typed'").fetchone()[0])
    assert cases == strs and stats["kept_cases"] == 0


def test_renamed_local_solution_is_not_duplicated(tmp_path):
    rebuild(tmp_path, CONTENT)
    renamed = tmp_path / "c"
    shutil.copytree(CONTENT, renamed)
    sol = renamed / "problems/count-vowels/solutions/01-scan.md"
    sol.write_text(sol.read_text().replace("title: Single scan", "title: One pass"))
    con, stats = rebuild(tmp_path, renamed)
    titles = [r[0] for r in con.execute("select title from solutions where slug='count-vowels'")]
    assert titles == ["One pass"] and stats["kept_solutions"] == 0


def test_local_solutions_kept_when_whole_folder_removed(tmp_path):
    rebuild(tmp_path, CONTENT)
    con, _ = rebuild(tmp_path, tmp_path / "empty")
    assert [r[0] for r in con.execute("select title from solutions where slug='count-vowels'")] == ["Single scan"]
