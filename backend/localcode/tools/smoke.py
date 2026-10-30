"""End-to-end smoke test against a running stack.

    python -m localcode.tools.smoke [--base-url http://localhost:4173]

Waits for the import, submits the reference Two Sum solution in every language (expects Accepted),
a wrong answer (expects Wrong Answer), and a Run with a custom case.
"""

import argparse
import sys
import time

from localcode.tools.client import DEFAULT_BASE_URL, LocalcodeClient

IMPORT_TIMEOUT_S = 3600
WRONG_TWO_SUM = (
    "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        return [0, 0]\n"
)


def wait_for_import(client: LocalcodeClient) -> dict:
    deadline = time.monotonic() + IMPORT_TIMEOUT_S
    while time.monotonic() < deadline:
        status = client.get("/api/status")
        if status["imported"] and not status["import"]["running"]:
            return status
        imp = status["import"]
        print(f"waiting for import: {imp['step']} {imp['done']}/{imp['total']}", flush=True)
        time.sleep(10)
    raise SystemExit("import did not finish")


def check(label: str, ok: bool, detail: object = "") -> None:
    print(f"{'ok ' if ok else 'FAIL'} {label} {detail}", flush=True)
    if not ok:
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    client = LocalcodeClient(ap.parse_args(argv).base_url)

    print("stats:", wait_for_import(client)["meta"]["stats"])
    reference = client.get("/api/problems/two-sum/solutions")[0]["code"]
    for lang in ("python", "java", "cpp", "kotlin"):
        _, r = client.submit("two-sum", lang, reference[lang])
        check(f"{lang} reference accepted", r.get("verdict") == "Accepted", f"{r.get('passed')}/{r.get('total')}")
    _, r = client.submit("two-sum", "python", WRONG_TWO_SUM)
    check("wrong answer detected", r.get("verdict") == "Wrong Answer")
    status, r = client.post(
        "/api/run",
        {"slug": "two-sum", "lang": "python", "code": reference["python"], "custom": ["nums = [1,2,3], target = 5"]},
    )
    check("run with custom case", status == 200 and r["verdict"] == "Accepted")
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
