"""End-to-end smoke test against a running stack: python3 scripts/smoke.py [base_url]"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4173"


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def main():
    for _ in range(360):
        _, s = call("GET", "/api/status")
        if s["imported"] and not s["import"]["running"]:
            break
        print("waiting for import:", s["import"]["step"], s["import"]["done"], "/", s["import"]["total"], flush=True)
        time.sleep(10)
    else:
        sys.exit("import did not finish")
    print("stats:", s["meta"]["stats"])
    _, sols = call("GET", "/api/problems/two-sum/solutions")
    code = sols[0]["code"]
    for lang in ("python", "java", "cpp", "kotlin"):
        st, r = call("POST", "/api/submit", {"slug": "two-sum", "lang": lang, "code": code[lang]})
        print(lang, st, r.get("verdict"), f"{r.get('passed')}/{r.get('total')}", r.get("compile_error") or "")
        assert r.get("verdict") == "Accepted", r
    wrong = "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        return [0, 0]\n"
    _, r = call("POST", "/api/submit", {"slug": "two-sum", "lang": "python", "code": wrong})
    assert r["verdict"] == "Wrong Answer", r
    st, r = call("POST", "/api/run", {"slug": "two-sum", "lang": "python", "code": code["python"],
                                      "custom": ["nums = [1,2,3], target = 5"]})
    assert st == 200 and r["verdict"] == "Accepted", r
    print("SMOKE OK")


if __name__ == "__main__":
    main()
