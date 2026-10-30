"""Submit doocs reference solutions for random problems and report pass rates per language.

python3 scripts/sample_refs.py [N] [out.json]
"""
import json
import random
import sys
import urllib.parse
from collections import Counter

sys.path.insert(0, "scripts")
import smoke  # noqa: E402

smoke.BASE = "http://localhost:4173"
call = smoke.call

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
OUT = sys.argv[2] if len(sys.argv) > 2 else "sample_refs.json"

slugs, page = [], 1
while True:
    _, r = call("GET", "/api/problems?" + urllib.parse.urlencode({"page": page, "page_size": 200}))
    slugs += [p["slug"] for p in r["items"] if p["has_tests"]]
    if page * 200 >= r["total"]:
        break
    page += 1
random.seed(7)
chosen = random.sample(slugs, min(N, len(slugs)))
results, verdicts = [], {lang: Counter() for lang in ("python", "java", "cpp", "kotlin")}
for i, slug in enumerate(chosen):
    _, detail = call("GET", f"/api/problems/{slug}")
    _, sols = call("GET", f"/api/problems/{slug}/solutions")
    for lang in detail["langs"]:
        sol = next((s for s in sols if lang in s["code"] and lang not in s["notes"]), None)
        if not sol:
            continue
        st, r = call("POST", "/api/submit", {"slug": slug, "lang": lang, "code": sol["code"][lang]})
        v = r.get("verdict") if st == 200 else f"HTTP {st}"
        verdicts[lang][v] += 1
        if v != "Accepted":
            results.append({"slug": slug, "lang": lang, "verdict": v, "passed": r.get("passed"), "total": r.get("total"),
                            "failing": r.get("failing"), "compile_error": (r.get("compile_error") or "")[:600]})
    print(i + 1, slug, {k: dict(v) for k, v in verdicts.items()}, flush=True)
json.dump({"verdicts": {k: dict(v) for k, v in verdicts.items()}, "failures": results}, open(OUT, "w"), indent=1)
print("DONE", {k: dict(v) for k, v in verdicts.items()})
