from localcode.judging import checkers
from localcode.tools.check_checkers import check


def test_reports_checkers_that_reject_the_expected_answer(data_dir, monkeypatch):
    monkeypatch.setitem(checkers.CHECKERS, "pair-sum", lambda args, expected, actual: actual[0] < actual[1])
    monkeypatch.setitem(checkers.CHECKERS, "tree-mirror", lambda args, expected, actual: False)
    report = check(data_dir / "content.db", excluded={})
    assert report["pair-sum"]["checked"] == 4 and report["pair-sum"]["rejected"] == []
    assert report["tree-mirror"]["rejected"] and report["tree-mirror"]["checked"] > 0


def test_skips_excluded_cases_and_flags_unknown_slugs(data_dir, monkeypatch):
    from localcode.importer.case_filter import case_key

    monkeypatch.setitem(checkers.CHECKERS, "pair-sum", lambda args, expected, actual: args[1] != 10)
    monkeypatch.setitem(checkers.CHECKERS, "no-such-problem", lambda args, expected, actual: True)
    excluded = {"pair-sum": {case_key([[1, 4, 6], 10]), case_key([[5, 5], 10])}}
    report = check(data_dir / "content.db", excluded=excluded)
    assert report["no-such-problem"]["error"] == "not a runnable problem"
    assert report["pair-sum"]["checked"] == 2 and report["pair-sum"]["rejected"] == []
