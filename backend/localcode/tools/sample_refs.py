"""Submit reference solutions for random problems and report pass rates per language.

    python -m localcode.tools.sample_refs [-n 100] [--out sample.json] [--base-url ...]

A drop in a language's pass rate points at a harness or data regression. Note: submissions are
recorded in the instance's user.db, so run this against a scratch instance.
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

from localcode.tools.client import DEFAULT_BASE_URL, LocalcodeClient

LANGS = ("python", "java", "cpp", "kotlin")
PAGE_SIZE = 200


def runnable_slugs(client: LocalcodeClient) -> list[str]:
    slugs, page = [], 1
    while True:
        r = client.get("/api/problems", page=page, page_size=PAGE_SIZE)
        slugs += [p["slug"] for p in r["items"] if p["has_tests"]]
        if page * PAGE_SIZE >= r["total"]:
            return slugs
        page += 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-n", type=int, default=100, help="number of problems to sample")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=Path("sample_refs.json"))
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = ap.parse_args(argv)
    client = LocalcodeClient(args.base_url)

    slugs = runnable_slugs(client)
    chosen = random.Random(args.seed).sample(slugs, min(args.n, len(slugs)))
    verdicts = {lang: Counter() for lang in LANGS}
    failures = []
    for i, slug in enumerate(chosen, 1):
        detail = client.get(f"/api/problems/{slug}")
        solutions = client.get(f"/api/problems/{slug}/solutions")
        for lang in detail["langs"]:
            # Only real references: Kotlin's Java fallback can't compile as Kotlin.
            sol = next((s for s in solutions if lang in s["code"] and lang not in s["notes"]), None)
            if not sol:
                continue
            status, r = client.submit(slug, lang, sol["code"][lang])
            verdict = r.get("verdict") if status == 200 else f"HTTP {status}"
            verdicts[lang][verdict] += 1
            if verdict != "Accepted":
                failures.append(
                    {
                        "slug": slug,
                        "lang": lang,
                        "verdict": verdict,
                        "failing": r.get("failing"),
                        "compile_error": (r.get("compile_error") or "")[:600],
                    }
                )
        print(i, slug, {k: dict(v) for k, v in verdicts.items() if v}, flush=True)
    summary = {k: dict(v) for k, v in verdicts.items()}
    args.out.write_text(json.dumps({"verdicts": summary, "failures": failures}, indent=1))
    print("DONE", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
