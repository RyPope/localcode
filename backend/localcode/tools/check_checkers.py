"""Maintainer tool: every answer checker must accept the dataset's own expected answers.

For each problem with a checker, runs the checker on every test case that is not on the exclusion
list, passing the expected value as the answer. A rejection means the checker is wrong (or the case
is invalid and belongs on the exclusion list). Run it against a content.db built from the sources:

    docker compose exec -T -u localcode app python -m localcode.tools.check_checkers [--only slug ...]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from localcode import config
from localcode.importer.build import load_excluded
from localcode.importer.case_filter import case_key
from localcode.judging.checkers import CHECKERS
from localcode.judging.compare import CHECKER_PREFIX, judge

MAX_REPORTED = 3


def check(db: Path, excluded: dict[str, set[str]] | None = None, only: list[str] | None = None) -> dict[str, dict]:
    """Per checked slug: how many cases were checked and the first few rejected ones."""
    excluded = load_excluded() if excluded is None else excluded
    con = sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True)
    report: dict[str, dict] = {}
    try:
        for slug in sorted(only or CHECKERS):
            row = con.execute(
                "select t.cases from problems p join tests t on t.slug = p.slug where p.slug = ? and p.has_tests = 1",
                (slug,),
            ).fetchone()
            if not row:
                report[slug] = {"error": "not a runnable problem"}
                continue
            skip = excluded.get(slug, set())
            cases = [c for c in json.loads(row[0]) if case_key(c["args"]) not in skip]
            mode = f"{CHECKER_PREFIX}{slug}"
            rejected = [c for c in cases if not judge(c["expected"], c["expected"], mode, c["args"])]
            report[slug] = {"checked": len(cases), "rejected": rejected[:MAX_REPORTED], "rejected_count": len(rejected)}
    finally:
        con.close()
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", type=Path, default=config.CONTENT_DB, help="content.db to read test cases from")
    ap.add_argument("--only", nargs="*", help="limit to these problem slugs")
    args = ap.parse_args(argv)
    report = check(args.db, only=args.only)
    bad = 0
    for slug, r in report.items():
        if "error" in r or r["rejected_count"]:
            bad += 1
            detail = (
                r.get("error")
                or f"rejects {r['rejected_count']}/{r['checked']}, e.g. {json.dumps(r['rejected'][0])[:300]}"
            )
            print(f"FAIL {slug}: {detail}")
        else:
            print(f"ok   {slug}: {r['checked']} cases")
    print(f"{len(report) - bad}/{len(report)} checkers accept every expected answer")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
