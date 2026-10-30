from localcode.judging.verdicts import grade_run, grade_submission


def res(values=(), **kw):
    base = {"compile_error": None, "timed_out": False, "memory_kb": 10, "exit_code": 0, "stderr": "",
            "results": [{"ok": True, "value": v, "stdout": "", "ms": 1.5} for v in values]}
    return {**base, **kw}


CASES = [{"args": [1], "expected": 1}, {"args": [2], "expected": 2}, {"args": [3], "expected": 3}]


def test_submission_accepted_sums_runtime():
    g = grade_submission(CASES, res([1, 2, 3]), "exact")
    assert (g.verdict, g.passed, g.runtime_ms) == ("Accepted", 3, 4.5)


def test_submission_stops_at_first_failure():
    g = grade_submission(CASES, res([1, 9, 9]), "exact")
    assert (g.verdict, g.passed) == ("Wrong Answer", 1)
    assert g.failing["args"] == [2] and g.failing["actual"] == 9


def test_submission_crash_reports_signal():
    g = grade_submission(CASES, res([1], exit_code=-11, stderr="boom"), "exact")
    assert g.verdict == "Runtime Error"
    assert g.failing["error"].startswith("Segmentation fault") and "boom" in g.failing["error"]


def test_submission_killed_process_is_memory_limit():
    assert grade_submission(CASES, res([], exit_code=-9), "exact").verdict == "Memory Limit Exceeded"


def test_run_reports_every_case_and_first_verdict():
    g = grade_run([[1], [2], [3]], [1, 2, 3], res([1, 0, 3]), "exact")
    assert [c.ok for c in g.cases] == [True, False, True]
    assert g.verdict == "Wrong Answer"


def test_run_without_reference_value_is_not_ok():
    g = grade_run([[1]], [None], res([1]), "exact")
    assert g.cases[0].ok is False and "Reference" in g.cases[0].error


def test_run_timeout_marks_missing_cases():
    g = grade_run([[1], [2]], [1, 2], res([1], timed_out=True), "exact")
    assert g.verdict == "Time Limit Exceeded"
    assert g.cases[1].ok is False
