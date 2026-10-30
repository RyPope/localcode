"""Company question lists (liquidslr/leetcode-company-wise-problems)."""
import csv
import re
from pathlib import Path
from typing import Iterator

WINDOWS = {"1": "30d", "2": "3m", "3": "6m", "4": "older", "5": "all"}
_SLUG_RE = re.compile(r"leetcode\.com/problems/([\w-]+)")


def company_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_companies(root: Path) -> Iterator[tuple[str, str, str, str, float, float | None]]:
    """Yields (company_slug, name, window, problem_slug, frequency, acceptance)."""
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        for f in sorted(folder.glob("*.csv")):
            window = WINDOWS.get(f.name.split(".", 1)[0])
            if not window:
                continue
            with open(f, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    m = _SLUG_RE.search(row.get("Link", ""))
                    if not m:
                        continue
                    try:
                        freq = float(row.get("Frequency") or 0)
                    except ValueError:
                        freq = 0.0
                    try:
                        acc = float(row["Acceptance Rate"]) if row.get("Acceptance Rate") else None
                    except ValueError:
                        acc = None
                    if acc is not None and acc <= 0.01:  # upstream stores 58% as 0.0058
                        acc *= 100
                    yield company_slug(folder.name), folder.name, window, m.group(1), freq, acc
