from pathlib import Path

from localcode.importer.companies import company_slug, load_companies

ROOT = Path(__file__).parent / "fixtures" / "companies"


def test_company_windows():
    rows = sorted(load_companies(ROOT))
    assert ("acme", "Acme", "30d", "pair-sum", 100.0, 0.55) in rows
    assert ("acme", "Acme", "all", "tree-mirror", 40.0, 0.61) in rows
    assert ("big-co", "Big Co", "6m", "list-reverse", 12.5, 0.7) in rows
    assert len(rows) == 4


def test_company_slug():
    assert company_slug("AQR Capital Management") == "aqr-capital-management"
    assert company_slug("J.P. Morgan") == "j-p-morgan"


def test_acceptance_rescaled_when_stored_as_hundredths(tmp_path):
    d = tmp_path / "X"
    d.mkdir()
    (d / "5. All.csv").write_text(
        "Difficulty,Title,Frequency,Acceptance Rate,Link,Topics\nEASY,T,1.0,0.0058,https://leetcode.com/problems/t,A\n"
    )
    (row,) = list(load_companies(tmp_path))
    assert abs(row[5] - 0.58) < 1e-9
