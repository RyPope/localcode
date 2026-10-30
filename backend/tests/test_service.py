import pytest

from localcode import db, service
from localcode.service import ServiceError


def ok(values, ms=2.0):
    return {"compile_error": None, "timed_out": False, "memory_kb": 2048, "exit_code": 0, "stderr": "",
            "results": [{"ok": True, "value": v, "stdout": "", "ms": ms} for v in values]}


def test_submit_accepted_records_submission(data_dir, runner):
    runner.user = ok([[1, 2], [0, 1], [0, 2], [0, 1]])
    r = service.submit(runner, "pair-sum", "python", "code")
    assert r["verdict"] == "Accepted"
    assert (r["passed"], r["total"]) == (4, 4)
    assert r["runtime_ms"] == 8.0 and r["memory_kb"] == 2048
    with db.connect_user() as u:
        row = u.execute("select verdict, passed, total, lang from submissions").fetchone()
    assert tuple(row) == ("Accepted", 4, 4, "python")
    assert runner.calls[0]["timeout_ms"] == 10000
    assert runner.calls[0]["ret"] == "List[int]"


def test_submit_wrong_answer_reports_first_failing(data_dir, runner):
    runner.user = ok([[1, 2], [9, 9], [0, 0], [0, 1]])
    r = service.submit(runner, "pair-sum", "python", "code")
    assert r["verdict"] == "Wrong Answer"
    assert r["passed"] == 1
    assert r["failing"] == {"args": [[5, 5], 10], "expected": [0, 1], "actual": [9, 9], "stdout": "", "error": None}


def test_timeout_maps_to_tle(data_dir, runner):
    runner.user = {**ok([[1, 2]]), "timed_out": True}
    r = service.submit(runner, "pair-sum", "python", "code")
    assert r["verdict"] == "Time Limit Exceeded"
    assert r["passed"] == 1
    assert r["failing"]["args"] == [[5, 5], 10]


def test_runtime_and_memory_errors(data_dir, runner):
    runner.user = {**ok([]), "results": [{"ok": False, "error": "ZeroDivisionError: x", "stdout": "", "ms": 0}]}
    assert service.submit(runner, "pair-sum", "python", "c")["verdict"] == "Runtime Error"
    runner.user = {**ok([]), "results": [{"ok": False, "error": "java.lang.OutOfMemoryError: heap", "stdout": "", "ms": 0}]}
    assert service.submit(runner, "pair-sum", "java", "c")["verdict"] == "Memory Limit Exceeded"
    runner.user = {**ok([]), "exit_code": -11}
    r = service.submit(runner, "pair-sum", "cpp", "c")
    assert r["verdict"] == "Runtime Error"
    assert "Segmentation fault" in r["failing"]["error"]


def test_compile_error(data_dir, runner):
    runner.user = {**ok([]), "compile_error": "solution.cpp:3: error: y"}
    r = service.submit(runner, "pair-sum", "cpp", "c")
    assert r["verdict"] == "Compile Error" and r["compile_error"].startswith("solution.cpp:3")


def test_cpp_request_carries_signature(data_dir, runner):
    runner.user = ok([[1, 2], [0, 1], [0, 2], [0, 1]])
    service.submit(runner, "pair-sum", "cpp", "code")
    assert runner.calls[0]["cpp_sig"]["method"] == "pairSum"


def test_run_uses_examples_plus_custom_and_reference_expected(data_dir, runner):
    runner.ref_values = {"[[1, 4, 6], 10]": [1, 2], "[[5, 5], 10]": [0, 1], "[[3, 7], 10]": [0, 1]}
    runner.user = ok([[1, 2], [0, 1], [1, 0]])
    r = service.run(runner, "pair-sum", "python", "code", ["nums = [3,7], goal = 10"])
    assert [c["expected"] for c in r["cases"]] == [[1, 2], [0, 1], [0, 1]]
    assert [c["ok"] for c in r["cases"]] == [True, True, False]
    assert r["verdict"] == "Wrong Answer"
    assert runner.calls[-1]["timeout_ms"] == 3 * 2000


def test_run_rejects_bad_custom_input(data_dir, runner):
    with pytest.raises(ServiceError) as e:
        service.run(runner, "pair-sum", "python", "code", ["nums = [3,7]"])
    assert e.value.status == 400 and "goal" in e.value.message
    with pytest.raises(ServiceError):
        service.run(runner, "pair-sum", "python", "code", ["nums = [3,"])


def test_language_not_available(data_dir, runner):
    with pytest.raises(ServiceError) as e:
        service.submit(runner, "tree-mirror", "java", "code")
    assert e.value.status == 400


def test_no_tests_problem_cannot_submit(data_dir, runner):
    with pytest.raises(ServiceError):
        service.submit(runner, "fill-in-place", "python", "code")


def test_status_derivation(data_dir, runner):
    assert service.problem_detail("pair-sum")["status"] == "todo"
    service.save_draft("pair-sum", "python", "x")
    assert service.problem_detail("pair-sum")["status"] == "attempted"
    runner.user = ok([[1, 2], [0, 1], [0, 2], [0, 1]])
    service.submit(runner, "pair-sum", "python", "code")
    assert service.problem_detail("pair-sum")["status"] == "solved"


def test_drafts_roundtrip(data_dir):
    assert service.get_draft("pair-sum", "java") is None
    service.save_draft("pair-sum", "java", "class Solution {}")
    assert service.get_draft("pair-sum", "java") == "class Solution {}"


def test_list_filters_by_company_window(data_dir):
    r = service.list_problems(company="acme", window="all")
    assert [p["slug"] for p in r["items"]] == ["pair-sum", "tree-mirror"]
    assert r["items"][0]["frequency"] == 80.5
    r = service.list_problems(company="acme", window="30d")
    assert [p["slug"] for p in r["items"]] == ["pair-sum"]
    r = service.list_problems(difficulty="Medium")
    assert [p["slug"] for p in r["items"]] == ["tree-mirror"]
    r = service.list_problems(q="reverse")
    assert [p["slug"] for p in r["items"]] == ["list-reverse"]
    assert service.list_problems()["counts"]["easy"] == [0, 3]


def test_problem_detail_shape(data_dir):
    p = service.problem_detail("pair-sum")
    assert p["langs"] == ["python", "java", "cpp", "kotlin"]
    assert set(p["starters"]) == {"python", "java", "cpp", "kotlin"}
    assert p["examples"] == [[[1, 4, 6], 10], [[5, 5], 10]]
    assert p["companies"][0]["slug"] == "acme"
    assert "ref_python" not in p


def test_solutions_kotlin_fallback_note(data_dir):
    sols = service.solutions("pair-sum")
    assert sols[0]["code"]["kotlin"] == sols[0]["code"]["java"]
    assert sols[0]["notes"]["kotlin"] == "No Kotlin reference yet — showing Java."
    assert sols[1]["code"]["kotlin"].startswith("class Solution")
    assert "kotlin" not in sols[1]["notes"]


def test_company_summary(data_dir):
    c = service.company_summary("acme", "all")
    assert c["name"] == "Acme" and c["total"] == 2
    assert c["by_difficulty"] == {"Easy": 1, "Medium": 1, "Hard": 0}
    assert c["windows"] == {"30d": 1, "3m": 0, "6m": 0, "older": 0, "all": 2}
    assert [p["slug"] for p in c["next_unsolved"]] == ["pair-sum", "tree-mirror"]


def test_stats_counts_first_accept(data_dir, runner):
    runner.user = ok([[1, 2], [0, 1], [0, 2], [0, 1]])
    service.submit(runner, "pair-sum", "python", "code")
    service.submit(runner, "pair-sum", "java", "code")
    s = service.stats()
    assert s["totals"]["easy"] == [1, 3]
    assert sum(w["easy"] for w in s["solved_by_week"]) == 1
