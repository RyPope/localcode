from localcode.importer.signatures import cpp_starter, java_starter, kotlin_starter, parse_cpp_sig, parse_java_sig


def test_java_sig_generic():
    sig = parse_java_sig("class Solution {\n    public List<List<Integer>> threeSum(int[] nums) {\n        return null;\n    }\n}")
    assert sig == {"method": "threeSum", "ret": "List<List<Integer>>", "params": [{"type": "int[]", "name": "nums"}]}


def test_java_sig_2d_and_multi():
    sig = parse_java_sig("import java.util.*;\nclass Solution {\n    private int x;\n    public int[][] merge(int[][] intervals, Map<String, List<Integer>> m) { return null; }\n}")
    assert sig["ret"] == "int[][]"
    assert sig["params"] == [{"type": "int[][]", "name": "intervals"}, {"type": "Map<String, List<Integer>>", "name": "m"}]


def test_java_sig_skips_comment_definitions():
    src = "/**\n * public class TreeNode {\n *     TreeNode(int val) { this.val = val; }\n * }\n */\nclass Solution {\n    public int maxDepth(TreeNode root) {\n        return 0;\n    }\n}"
    assert parse_java_sig(src)["params"] == [{"type": "TreeNode", "name": "root"}]


def test_cpp_sig_refs():
    sig = parse_cpp_sig("class Solution {\npublic:\n    vector<vector<int>> merge(vector<vector<int>>& intervals) {\n        return {};\n    }\n};")
    assert sig == {"method": "merge", "ret": "vector<vector<int>>", "params": [{"type": "vector<vector<int>>&", "name": "intervals"}]}


def test_cpp_sig_pointer_and_const():
    sig = parse_cpp_sig("class Solution {\npublic:\n    ListNode* reverse(ListNode* head, const string& s, int k) {\n        return head;\n    }\n};")
    assert sig["ret"] == "ListNode*"
    assert sig["params"] == [{"type": "ListNode*", "name": "head"}, {"type": "const string&", "name": "s"}, {"type": "int", "name": "k"}]


def test_kotlin_starter_merge():
    sig = {"method": "merge", "ret": "int[][]", "params": [{"type": "int[][]", "name": "intervals"}]}
    assert kotlin_starter(sig) == "class Solution {\n    fun merge(intervals: Array<IntArray>): Array<IntArray> {\n        \n    }\n}\n"


def test_kotlin_starter_tree():
    sig = {"method": "maxDepth", "ret": "int", "params": [{"type": "TreeNode", "name": "root"}]}
    out = kotlin_starter(sig)
    assert "fun maxDepth(root: TreeNode?): Int {" in out
    assert "class TreeNode(var `val`: Int)" in out


def test_kotlin_types():
    sig = {"method": "f", "ret": "List<List<String>>", "params": [
        {"type": "char[][]", "name": "g"}, {"type": "List<Integer>", "name": "a"}, {"type": "long", "name": "n"}, {"type": "String[]", "name": "w"}]}
    assert "fun f(g: Array<CharArray>, a: List<Int>, n: Long, w: Array<String>): List<List<String>> {" in kotlin_starter(sig)


def test_java_starter():
    sig = {"method": "merge", "ret": "int[][]", "params": [{"type": "int[][]", "name": "intervals"}]}
    assert java_starter(sig) == "class Solution {\n    public int[][] merge(int[][] intervals) {\n        \n    }\n}\n"


def test_cpp_starter_with_listnode_comment():
    sig = {"method": "reverse", "ret": "ListNode*", "params": [{"type": "ListNode*", "name": "head"}]}
    out = cpp_starter(sig)
    assert out.endswith("class Solution {\npublic:\n    ListNode* reverse(ListNode* head) {\n        \n    }\n};\n")
    assert "struct ListNode" in out


def test_cpp_sig_long_long():
    sig = parse_cpp_sig("class Solution {\npublic:\n    long long countPairs(vector<long long>& a, unsigned int k) {\n        return 0;\n    }\n};")
    assert sig == {"method": "countPairs", "ret": "long long",
                   "params": [{"type": "vector<long long>&", "name": "a"}, {"type": "unsigned int", "name": "k"}]}
