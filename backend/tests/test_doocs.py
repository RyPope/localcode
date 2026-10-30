from pathlib import Path

from localcode.importer.doocs import iter_problem_dirs, parse_problem_dir

ROOT = Path(__file__).parent / "fixtures" / "doocs"


def problem():
    (d,) = list(iter_problem_dirs(ROOT))
    return parse_problem_dir(d)


def test_parse_readme_fields():
    p = problem()
    assert p.slug == "pair-sum"
    assert p.frontend_id == 7
    assert p.title == "Pair Sum"
    assert p.difficulty == "Easy"
    assert p.tags == ["Array", "Hash Table"]
    assert p.description_html.strip() == "<p>Find two indices whose values add up to <code>goal</code>.</p>"


def test_solutions_split_by_heading():
    p = problem()
    assert [s["title"] for s in p.solutions] == ["Hash Map", "Solution 2"]
    s1 = p.solutions[0]
    assert set(s1["code"]) == {"python", "java", "cpp"}
    assert "public int[] pairSum" in s1["code"]["java"]
    assert "Store each value's index" in s1["explanation_md"]
    assert "Think about complements" in s1["explanation_md"]
    assert "tabs:start" not in s1["explanation_md"]
    assert set(p.solutions[1]["code"]) == {"python", "kotlin"}


def test_first_code_per_language():
    p = problem()
    assert "public int[] pairSum" in p.first_code("java")
    assert "intArrayOf" in p.first_code("kotlin")
    assert p.first_code("rust") is None
