"""Python harness: py_driver.py <solution.py> <cases.json> <results.jsonl>"""

import io
import json
import sys
import threading
import time
import traceback

PRELUDE = """
import random, functools, collections, string, math, datetime, re, heapq, bisect, itertools, operator
from typing import *
from functools import *
from collections import *
from itertools import *
from heapq import *
from bisect import *
from string import *
from operator import *
from math import *
inf = float('inf')

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""
MAX_STDOUT = 64 * 1024
MAX_NODES = 200_000


def build_list(ns, values):
    head = cur = None
    for v in values:
        node = ns["ListNode"](v)
        if cur is None:
            head = node
        else:
            cur.next = node
        cur = node
    return head


def build_tree(ns, values):
    if not values or values[0] is None:
        return None
    TreeNode = ns["TreeNode"]
    root = TreeNode(values[0])
    queue, i = [root], 1
    for node in queue:
        if i >= len(values):
            break
        if values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root


def convert_in(ns, value, typ):
    typ = typ.strip()
    if typ == "ListNode":
        return build_list(ns, value)
    if typ == "TreeNode":
        return build_tree(ns, value)
    if typ.startswith("List[") and isinstance(value, list):
        return [convert_in(ns, v, typ[5:-1]) for v in value]
    return value


def convert_out(ns, value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, ns["ListNode"]):
        out, n = [], 0
        while value is not None and n < MAX_NODES:
            out.append(value.val)
            value, n = value.next, n + 1
        return out
    if isinstance(value, ns["TreeNode"]):
        out, queue = [], [value]
        for node in queue:
            if len(out) > MAX_NODES:
                break
            if node is None:
                out.append(None)
            else:
                out.append(node.val)
                queue.extend([node.left, node.right])
        while out and out[-1] is None:
            out.pop()
        return out
    if isinstance(value, (list, tuple)):
        return [convert_out(ns, v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(convert_out(ns, v) for v in value)
    return str(value)


def user_traceback(exc: BaseException) -> str:
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "solution.py"]
    where = f"\n  line {frames[-1].lineno}, in {frames[-1].name}" if frames else ""
    return f"{type(exc).__name__}: {exc}{where}"


def main(sol_path, cases_path, out_path):
    with open(cases_path) as f:
        spec = json.load(f)
    with open(sol_path) as f:
        source = f.read()
    with open(out_path, "w") as out:
        _run_cases(spec, source, out)


def _run_cases(spec, source, out):
    def emit(obj):
        out.write(json.dumps(obj) + "\n")
        out.flush()

    ns = {"__name__": "solution"}
    try:
        exec(compile(PRELUDE, "prelude", "exec"), ns)
        exec(compile(source, "solution.py", "exec"), ns)
        getattr(ns["Solution"], spec["method"])
    except SyntaxError as e:
        emit({"compile_error": f"SyntaxError: {e.msg} (line {e.lineno})"})
        return
    except Exception as e:
        emit(
            {
                "compile_error": f"{type(e).__name__}: {e}"
                if not isinstance(e, (KeyError, AttributeError))
                else f"class Solution with method {spec['method']} not found"
            }
        )
        return

    types = [p["type"] for p in spec["params"]]
    real_stdout = sys.stdout
    for args in spec["cases"]:
        buf = io.StringIO()
        sys.stdout = buf
        try:
            conv = [convert_in(ns, a, t) for a, t in zip(args, types, strict=False)]
            method = getattr(ns["Solution"](), spec["method"])
            t0 = time.perf_counter()
            result = method(*conv)
            ms = (time.perf_counter() - t0) * 1000
            if result is None and spec.get("ret") in ("ListNode", "TreeNode"):
                result = []
            line = {"ok": True, "value": convert_out(ns, result), "ms": round(ms, 3)}
        except BaseException as e:
            line = {"ok": False, "error": user_traceback(e), "ms": 0}
        finally:
            sys.stdout = real_stdout
        line["stdout"] = buf.getvalue()[:MAX_STDOUT]
        emit(line)


if __name__ == "__main__":
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(128 * 1024 * 1024)
    t = threading.Thread(target=main, args=sys.argv[1:4])
    t.start()
    t.join()
