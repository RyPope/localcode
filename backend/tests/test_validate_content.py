import json
from pathlib import Path

from localcode.tools.validate_content import validate

CONTENT = Path(__file__).parent / "fixtures" / "content"


class Runner:
    """Answers every language with `answers[json args]`, except languages listed in `wrong`."""

    def __init__(self, answers: dict, wrong: tuple[str, ...] = (), compile_error: str | None = None):
        self.answers, self.wrong, self.compile_error = answers, wrong, compile_error
        self.langs: list[str] = []

    def __call__(self, req, endpoint=None):
        self.langs.append(req["lang"])
        if self.compile_error and req["lang"] == "java":
            return {"compile_error": self.compile_error, "results": []}
        return {
            "compile_error": None,
            "results": [
                {"ok": True, "value": -1 if req["lang"] in self.wrong else self.answers[json.dumps(a)]}
                for a in req["cases"]
            ],
        }


VOWELS = {json.dumps(["hello"]): 2, json.dumps(["xyz"]): 0, json.dumps(["aeiou"]): 5}


def test_passing_problem_runs_every_language_and_reports_only_bad_folders():
    runner = Runner(VOWELS)
    errors = validate(CONTENT, execute=runner)
    assert sorted(runner.langs) == ["java", "python"]
    assert len(errors) == 1 and "broken/problem.md" in errors[0] and "difficulty" in errors[0]


def test_wrong_solution_names_problem_solution_language_and_case():
    errors = validate(CONTENT, execute=Runner(VOWELS, wrong=("java",)))
    [err] = [e for e in errors if "count-vowels" in e]
    assert "Single scan" in err and "java" in err and "case 1" in err and "expected 2" in err


def test_compile_error_reported():
    errors = validate(CONTENT, execute=Runner(VOWELS, compile_error="boom"))
    assert any("count-vowels" in e and "boom" in e for e in errors)


def test_unrunnable_new_problem_explains_why(tmp_path):
    d = tmp_path / "problems" / "too-few"
    (d / "solutions").mkdir(parents=True)
    (d / "tests.json").write_text(json.dumps([{"args": [1], "expected": 1}]))
    (d / "solutions" / "a.md").write_text(
        "---\ntitle: A\n---\n```python\nclass Solution:\n    def f(self, n: int) -> int:\n        return n\n```\n"
    )
    [err] = validate(tmp_path, execute=Runner({}))
    assert "too-few" in err and "3 test cases" in err


def test_solution_only_overlay_checks_signature_parses(tmp_path):
    d = tmp_path / "problems" / "two-sum" / "solutions"
    d.mkdir(parents=True)
    (d / "a.md").write_text("---\ntitle: A\n---\n```java\nnot java at all\n```\n")
    [err] = validate(tmp_path, execute=Runner({}))
    assert "two-sum" in err and "java" in err


def test_repo_examples_pass_offline_checks():
    root = Path(__file__).resolve().parents[2] / "content"
    answers = {
        json.dumps(c["args"]): c["expected"]
        for c in json.loads((root / "problems/longest-vowel-run/tests.json").read_text())
    }
    runner = Runner(answers)
    assert validate(root, execute=runner) == []
    assert sorted(runner.langs) == ["cpp", "java", "kotlin", "python"]
