import time

TWO_SUM = """class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        d = {}
        for i, x in enumerate(nums):
            if target - x in d:
                return [d[target - x], i]
            d[x] = i
"""
P2 = [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}]


def test_python_accepts(run):
    r = run("python", TWO_SUM, "twoSum", P2, [[[2, 7, 11, 15], 9], [[3, 3], 6]])
    assert r["compile_error"] is None
    assert [x["value"] for x in r["results"]] == [[0, 1], [0, 1]]
    assert all(x["ok"] for x in r["results"])
    assert r["memory_kb"] > 0


def test_python_tree_roundtrip(run):
    code = """class Solution:
    def invert(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if root:
            root.left, root.right = self.invert(root.right), self.invert(root.left)
        return root
"""
    r = run(
        "python",
        code,
        "invert",
        [{"name": "root", "type": "TreeNode"}],
        [[[4, 2, 7, 1, 3]], [[]], [[1, None, 2]]],
        ret="TreeNode",
    )
    assert [x["value"] for x in r["results"]] == [[4, 7, 2, None, None, 3, 1], [], [1, 2]]


def test_python_linked_list(run):
    code = """class Solution:
    def rev(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev
"""
    r = run("python", code, "rev", [{"name": "head", "type": "ListNode"}], [[[1, 2, 3]], [[]]], ret="ListNode")
    assert [x["value"] for x in r["results"]] == [[3, 2, 1], []]


def test_python_list_of_trees_param(run):
    code = """class Solution:
    def sizes(self, trees: List[TreeNode]) -> List[int]:
        def n(t):
            return 0 if not t else 1 + n(t.left) + n(t.right)
        return [n(t) for t in trees]
"""
    r = run("python", code, "sizes", [{"name": "trees", "type": "List[TreeNode]"}], [[[[1, 2], [3]]]])
    assert r["results"][0]["value"] == [2, 1]


def test_stdout_is_captured_per_case(run):
    code = """class Solution:
    def f(self, x: int) -> int:
        print("saw", x)
        return x * 2
"""
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1], [2]])
    assert [x["stdout"] for x in r["results"]] == ["saw 1\n", "saw 2\n"]
    assert [x["value"] for x in r["results"]] == [2, 4]


def test_runtime_error_reported(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        return 1 // x\n"
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1], [0], [2]])
    assert r["results"][0]["ok"] is True
    assert r["results"][1]["ok"] is False
    assert "ZeroDivisionError" in r["results"][1]["error"]
    assert "line 3" in r["results"][1]["error"]
    assert r["results"][2]["value"] == 0


def test_syntax_error_is_compile_error(run):
    r = run("python", "class Solution:\n    def f(self x):\n", "f", [{"name": "x", "type": "int"}], [[1]])
    assert "SyntaxError" in r["compile_error"]
    assert r["results"] == []


def test_missing_method_is_compile_error(run):
    r = run("python", "class Solution:\n    pass\n", "f", [{"name": "x", "type": "int"}], [[1]])
    assert "f" in r["compile_error"]


def test_infinite_loop_times_out(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        while True:\n            pass\n"
    t = time.time()
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1], [2]], timeout_ms=2000)
    assert r["timed_out"] is True
    assert r["results"] == []
    assert time.time() - t < 5


def test_runner_survives_timeout(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        while True:\n            pass\n"
    run("python", code, "f", [{"name": "x", "type": "int"}], [[1]], timeout_ms=500)
    r = run("python", TWO_SUM, "twoSum", P2, [[[3, 3], 6]])
    assert r["results"][0]["value"] == [0, 1]


def test_memory_limit(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        a = [0] * (10 ** 9)\n        return len(a)\n"
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1]])
    assert r["results"][0]["ok"] is False
    assert "MemoryError" in r["results"][0]["error"]


def test_deep_recursion_allowed(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        return 0 if x == 0 else 1 + self.f(x - 1)\n"
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[50000]])
    assert r["results"][0]["value"] == 50000


def test_sandbox_cannot_write_outside_tmp(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        open('/srv/pwned', 'w').write('x')\n        return 1\n"
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1]])
    assert r["results"][0]["ok"] is False
