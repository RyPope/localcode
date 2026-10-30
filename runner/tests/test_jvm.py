def test_java_two_sum(run):
    code = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> d = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            if (d.containsKey(target - nums[i])) return new int[]{d.get(target - nums[i]), i};
            d.put(nums[i], i);
        }
        return new int[0];
    }
}"""
    r = run(
        "java",
        code,
        "twoSum",
        [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}],
        [[[2, 7, 11, 15], 9], [[3, 3], 6]],
    )
    assert r["compile_error"] is None, r
    assert [x["value"] for x in r["results"]] == [[0, 1], [0, 1]]


def test_java_list_of_lists(run):
    code = """class Solution {
    public List<List<Integer>> pairs(List<Integer> a, String[] tags) {
        List<List<Integer>> out = new ArrayList<>();
        for (int i = 0; i + 1 < a.size(); i += 2) out.add(Arrays.asList(a.get(i), a.get(i + 1)));
        out.add(List.of(tags.length));
        return out;
    }
}"""
    r = run(
        "java",
        code,
        "pairs",
        [{"name": "a", "type": "List[int]"}, {"name": "tags", "type": "List[str]"}],
        [[[1, 2, 3, 4], ["x", "y"]]],
    )
    assert r["results"][0]["value"] == [[1, 2], [3, 4], [2]]


def test_java_char_grid(run):
    code = """class Solution {
    public char first(char[][] grid, List<List<String>> words) {
        grid[0][0] = 'z';
        return grid[0][0];
    }
    public boolean other() { return false; }
}"""
    r = run(
        "java",
        code,
        "first",
        [{"name": "grid", "type": "List[List[str]]"}, {"name": "words", "type": "List[List[str]]"}],
        [[[["a", "b"], ["c", "d"]], [["hi"]]]],
    )
    assert r["results"][0]["value"] == "z"


def test_java_tree(run):
    code = """class Solution {
    public TreeNode invert(TreeNode root) {
        if (root == null) return null;
        TreeNode l = invert(root.left);
        root.left = invert(root.right);
        root.right = l;
        return root;
    }
}"""
    r = run("java", code, "invert", [{"name": "root", "type": "TreeNode"}], [[[4, 2, 7, 1, 3]], [[]]], ret="TreeNode")
    assert [x["value"] for x in r["results"]] == [[4, 7, 2, None, None, 3, 1], []]


def test_java_linked_list(run):
    code = """class Solution {
    public ListNode rev(ListNode head) {
        ListNode prev = null;
        while (head != null) { ListNode n = head.next; head.next = prev; prev = head; head = n; }
        return prev;
    }
}"""
    r = run("java", code, "rev", [{"name": "head", "type": "ListNode"}], [[[1, 2, 3]], [[]]], ret="ListNode")
    assert [x["value"] for x in r["results"]] == [[3, 2, 1], []]


def test_java_compile_error(run):
    r = run("java", "class Solution { public int f(int x) { return y; } }", "f", [{"name": "x", "type": "int"}], [[1]])
    assert "error:" in r["compile_error"]
    assert "/tmp" not in r["compile_error"]


def test_java_runtime_error(run):
    code = "class Solution { public int f(int[] a) { return a[5]; } }"
    r = run("java", code, "f", [{"name": "a", "type": "List[int]"}], [[[1]]])
    assert r["results"][0]["ok"] is False
    assert "ArrayIndexOutOfBoundsException" in r["results"][0]["error"]


def test_java_stdout_is_captured_per_case(run):
    code = 'class Solution { public int f(int x) { System.out.println("saw " + x); return x * 2; } }'
    r = run("java", code, "f", [{"name": "x", "type": "int"}], [[1], [2]])
    assert [x["stdout"] for x in r["results"]] == ["saw 1\n", "saw 2\n"]
    assert [x["value"] for x in r["results"]] == [2, 4]


def test_java_long_and_double(run):
    code = "class Solution { public double avg(long a, long b) { return (a + b) / 2.0; } }"
    r = run("java", code, "avg", [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}], [[10000000000, 3]])
    assert r["results"][0]["value"] == 5000000001.5


def test_java_boolean_and_string(run):
    code = "class Solution { public boolean same(String s, String t) { return s.equals(t); } }"
    r = run(
        "java", code, "same", [{"name": "s", "type": "str"}, {"name": "t", "type": "str"}], [["ab", "ab"], ["a", "b"]]
    )
    assert [x["value"] for x in r["results"]] == [True, False]


def test_java_infinite_loop_times_out(run):
    code = "class Solution { public int f(int x) { while (true) {} } }"
    r = run("java", code, "f", [{"name": "x", "type": "int"}], [[1]], timeout_ms=1000)
    assert r["timed_out"] is True


def test_kotlin_merge_intervals(run):
    code = """class Solution {
    fun merge(intervals: Array<IntArray>): Array<IntArray> {
        intervals.sortBy { it[0] }
        val out = mutableListOf<IntArray>()
        for (iv in intervals) {
            if (out.isNotEmpty() && out.last()[1] >= iv[0]) out.last()[1] = maxOf(out.last()[1], iv[1])
            else out.add(iv)
        }
        return out.toTypedArray()
    }
}"""
    r = run("kotlin", code, "merge", [{"name": "intervals", "type": "List[List[int]]"}], [[[[1, 3], [2, 6], [8, 10]]]])
    assert r["compile_error"] is None, r
    assert r["results"][0]["value"] == [[1, 6], [8, 10]]


def test_kotlin_tree_and_list(run):
    code = """class Solution {
    fun depth(root: TreeNode?, xs: List<Int>): Int {
        if (root == null) return xs.size
        return 1 + maxOf(depth(root.left, xs), depth(root.right, xs))
    }
}"""
    r = run(
        "kotlin",
        code,
        "depth",
        [{"name": "root", "type": "TreeNode"}, {"name": "xs", "type": "List[int]"}],
        [[[3, 9, 20, None, None, 15, 7], []]],
    )
    assert r["results"][0]["value"] == 3


def test_kotlin_compile_error(run):
    r = run("kotlin", "class Solution { fun f(x: Int): Int = y }", "f", [{"name": "x", "type": "int"}], [[1]])
    assert "error" in r["compile_error"]


def test_java_pair_is_available_without_import(run):
    code = """class Solution {
    public int f(int x) {
        Pair<Integer, String>[] t = new Pair[1];
        t[0] = new Pair<>(x, "a");
        return t[0].getKey() + t[0].getValue().length();
    }
}"""
    r = run("java", code, "f", [{"name": "x", "type": "int"}], [[41]])
    assert r["compile_error"] is None, r
    assert r["results"][0]["value"] == 42


def test_python_has_a_gigabyte(run):
    code = "class Solution:\n    def f(self, x: int) -> int:\n        a = bytearray(700 * 1024 * 1024)\n        return len(a) // (1024 * 1024)\n"
    r = run("python", code, "f", [{"name": "x", "type": "int"}], [[1]])
    assert r["results"][0]["value"] == 700
