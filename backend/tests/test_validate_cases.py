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


def test_references_failing_exactly_the_same_cases_exclude_them_even_when_most_fail():
    # Mostly-invalid suites (inputs that break the constraints) leave every reference below the
    # trusted bar; two references agreeing case for case is still strong evidence.
    failing = set(range(6))
    outcomes = {"java": passing_all_but(10, *failing), "cpp": passing_all_but(10, *failing)}
    assert cases_to_exclude(outcomes) == failing


def test_agreement_needs_two_references_and_three_surviving_cases():
    assert cases_to_exclude({"java": passing_all_but(10, *range(6))}) == set()
    both = passing_all_but(10, *range(8))
    assert cases_to_exclude({"java": both, "cpp": list(both)}) == set()
    disagree = {"java": passing_all_but(10, *range(6)), "cpp": passing_all_but(10, *range(1, 8))}
    assert cases_to_exclude(disagree) == set()


def test_fresh_run_ignores_previous_output(tmp_path, monkeypatch):
    import json

    from localcode.tools import validate_cases

    out = tmp_path / "excluded.json"
    out.write_text('{"stale-problem": ["abc"]}')
    out.with_suffix(".order.json").write_text('{"stale-problem": 3}')
    monkeypatch.setattr(validate_cases, "_runnable_slugs", lambda: ["pair-sum"])
    monkeypatch.setattr(validate_cases, "_validate_one", lambda slug, url: (["k1"], {"java": "3/4"}, 0, True))
    monkeypatch.setattr(validate_cases.runner_client, "endpoints", lambda: ["unix:test"])

    assert validate_cases.validate(out, fresh=True) == {"pair-sum": ["k1"]}
    assert json.loads(out.with_suffix(".order.json").read_text()) == {}
    assert json.loads(out.with_suffix(".review.json").read_text()) == {"pair-sum": [1, 4]}
    out.write_text('{"kept": []}')
    assert validate_cases.validate(out) == {"kept": [], "pair-sum": ["k1"]}


def test_exclusions_without_a_trusted_reference_need_review():
    from localcode.tools.validate_cases import needs_review

    most_fail = {"java": passing_all_but(10, *range(6)), "cpp": passing_all_but(10, *range(6))}
    assert needs_review(most_fail)
    assert not needs_review({"java": passing_all_but(10, 1), "cpp": passing_all_but(10, 1)})
    assert not needs_review({"java": passing_all_but(10, *range(8))})  # nothing excluded


def test_cases_whose_own_answer_fails_the_checker_are_unjudgeable(monkeypatch):
    from localcode.judging import checkers
    from localcode.tools.validate_cases import unjudgeable_cases

    monkeypatch.setitem(checkers.CHECKERS, "test-even", lambda args, expected, actual: actual % 2 == 0)
    cases = [{"args": [1], "expected": 2}, {"args": [2], "expected": 3}, {"args": [3], "expected": 4}]
    assert unjudgeable_cases(cases, "checker:test-even") == {1}
    assert unjudgeable_cases(cases, "exact") == set()
