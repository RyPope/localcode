from pathlib import Path

from localcode.importer.local import load_local

CONTENT = Path(__file__).parent / "fixtures" / "content"


def test_parses_new_problem():
    problems, _ = load_local(CONTENT)
    p = problems["count-vowels"]
    assert p.title == "Count Vowels" and p.difficulty == "Easy" and p.tags == ["String"]
    assert p.frontend_id is None and p.compare_mode is None
    assert "<p>Given a string <code>s</code>" in p.description_html
    assert len(p.cases) == 3 and p.cases[0] == {"args": ["hello"], "expected": 2}
    [sol] = p.solutions
    assert sol.title == "Single scan"
    assert set(sol.code) == {"python", "java"}
    assert sol.code["python"].startswith("class Solution:")
    assert "```" not in sol.explanation_md and "$O(n)$" in sol.explanation_md


def test_overlay_only_solutions():
    problems, _ = load_local(CONTENT)
    p = problems["pair-sum"]
    assert p.title is None and p.difficulty is None and p.tags is None
    assert p.description_html is None and p.cases is None
    assert [s.title for s in p.solutions] == ["Brute force"]
    assert set(p.solutions[0].code) == {"cpp"}


def test_bad_folder_skipped_with_reason():
    problems, skipped = load_local(CONTENT)
    assert "broken" not in problems
    [entry] = skipped
    assert entry["path"].endswith("broken/problem.md")
    assert "difficulty" in entry["reason"]


def test_invalid_entries_are_reported(tmp_path):
    root = tmp_path / "problems"
    (root / "Bad_Slug").mkdir(parents=True)
    (root / "bad-tests").mkdir()
    (root / "bad-tests" / "tests.json").write_text('[{"args": 1}]')
    (root / "bad-yaml").mkdir()
    (root / "bad-yaml" / "problem.md").write_text("---\ntitle: [unclosed\n---\nx\n")
    (root / "no-title" / "solutions").mkdir(parents=True)
    (root / "no-title" / "solutions" / "a.md").write_text("```python\nx\n```\n")
    (root / "unknown-key").mkdir()
    (root / "unknown-key" / "problem.md").write_text("---\ntitel: Typo\n---\n")
    problems, skipped = load_local(tmp_path)
    assert problems == {}
    reasons = {Path(e["path"]).relative_to(root).parts[0]: e["reason"] for e in skipped}
    assert set(reasons) == {"Bad_Slug", "bad-tests", "bad-yaml", "no-title", "unknown-key"}
    assert "titel" in reasons["unknown-key"]


def test_missing_root_is_empty(tmp_path):
    assert load_local(tmp_path / "nope") == ({}, [])


def test_unclosed_front_matter_is_reported(tmp_path):
    d = tmp_path / "problems" / "open-front"
    d.mkdir(parents=True)
    (d / "problem.md").write_text("---\ntitle: X\ndifficulty: Easy\n\nStatement.\n")
    problems, [entry] = load_local(tmp_path)
    assert problems == {} and "closing ---" in entry["reason"]
