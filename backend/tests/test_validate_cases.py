from localcode.tools.validate_cases import cases_to_exclude


def passing_all_but(n: int, *failing: int) -> list[bool]:
    return [i not in failing for i in range(n)]


def test_a_confident_reference_excludes_on_its_own():
    # A correct typed solution can fail an invalid case in one language while another gets lucky
    # (C++ often reads out of bounds without crashing), so one confident failure is enough.
    outcomes = {"java": passing_all_but(10, 2), "cpp": passing_all_but(10, 5)}
    assert cases_to_exclude(outcomes) == {2, 5}


def test_less_confident_references_must_agree():
    # Each passes 80%: on its own that could be a buggy reference, so only shared failures count.
    outcomes = {"java": passing_all_but(10, 1, 2), "cpp": passing_all_but(10, 2, 3)}
    assert cases_to_exclude(outcomes) == {2}


def test_a_single_trusted_reference_still_decides():
    # Suites with many invalid cases leave the only reference below the confident bar.
    assert cases_to_exclude({"java": passing_all_but(10, 1, 2)}) == {1, 2}


def test_confident_and_less_confident_references_combine():
    outcomes = {"java": passing_all_but(10, 3), "cpp": passing_all_but(10, 0, 1, 2, 4, 6)}
    assert cases_to_exclude(outcomes) == {3}


def test_untrusted_references_are_ignored():
    outcomes = {"java": passing_all_but(10, 4), "cpp": passing_all_but(10, *range(6))}
    assert cases_to_exclude(outcomes) == {4}
    assert cases_to_exclude({"java": [False, False, True]}) == set()
    assert cases_to_exclude({}) == set()


def test_order_only_differences_are_flagged():
    from localcode.tools.validate_cases import differs_only_in_order

    assert differs_only_in_order([[-1, 0, 1], [-1, -1, 2]], [[-1, -1, 2], [0, -1, 1]], "exact", [])
    assert not differs_only_in_order([[1, 2]], [[1, 2]], "exact", [])  # not a failure at all
    assert not differs_only_in_order([[1, 2]], [[1, 3]], "exact", [])  # a real difference
    assert not differs_only_in_order([[1, 2], [3]], [[2, 1], [3]], "any_order_deep", [])


def test_from_sources_builds_an_unfiltered_database(tmp_path, monkeypatch):
    import json
    import shutil
    import sqlite3
    from pathlib import Path

    from localcode import db
    from localcode.tools.validate_cases import prepare_from_sources

    fix = Path(__file__).parent / "fixtures"
    src = tmp_path / "sources"
    (src / "dataset").mkdir(parents=True)
    shutil.copy(fix / "dataset_rows.jsonl", src / "dataset" / "LeetCodeDataset-train.jsonl")
    shutil.copytree(fix / "doocs", src / "doocs")
    monkeypatch.setattr(db, "CONTENT_DB", tmp_path / "unused.db")
    monkeypatch.setattr(db, "USER_DB", tmp_path / "unused-user.db")
    monkeypatch.setattr("localcode.importer.build.load_excluded", lambda: {"pair-sum": {"anything"}})

    work = tmp_path / "work"
    prepare_from_sources(src, work)
    prepare_from_sources(src, work)  # rebuilds from scratch rather than carrying the old database forward

    assert (work / "content.db", work / "user.db") == (db.CONTENT_DB, db.USER_DB)
    con = sqlite3.connect(db.CONTENT_DB)
    cases = con.execute("select cases from tests where slug = 'pair-sum'").fetchone()[0]
    assert len(json.loads(cases)) == 4


def test_checker_rejections_are_never_order_only(monkeypatch):
    from localcode.judging import checkers
    from localcode.tools.validate_cases import differs_only_in_order

    # On an invalid input the reference repeats the recorded (invalid) answer; the checker rejects it.
    monkeypatch.setitem(checkers.CHECKERS, "test-strict", lambda args, expected, actual: False)
    assert not differs_only_in_order([1, 2], [1, 2], "checker:test-strict", [])
    assert not differs_only_in_order([1, 2], [2, 1], "checker:test-strict", [])


def test_order_only_cases_are_reported_but_still_fail(monkeypatch):
    from localcode.judging import runner_client
    from localcode.tools import validate_cases

    values = [[[1, 2]], [[2, 1]], [[9]]]
    monkeypatch.setattr(
        runner_client,
        "execute",
        lambda req, url=None: {"compile_error": None, "results": [{"ok": True, "value": v} for v in values]},
    )
    problem = {"method": "f", "params": "[]", "ret": "List[List[int]]", "compare_mode": "exact"}
    cases = [{"args": [i], "expected": [[1, 2]]} for i in range(3)]
    ok, order_only = validate_cases._outcomes(problem, "java", "code", cases, None, "unix:test")
    assert ok == [True, False, False]
    assert order_only == [False, True, False]
