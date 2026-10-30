import pytest
from harness.cpp_gen import gen_main


def sig(method, ret, *params):
    return {"method": method, "ret": ret, "params": [{"type": t, "name": n} for t, n in params]}


def test_gen_main_strips_refs_for_locals():
    src = gen_main(
        "class Solution {};",
        sig("merge", "vector<vector<int>>", ("vector<vector<int>>&", "iv"), ("const string&", "s")),
    )
    assert "lc::conv<vector<vector<int>>>::from(c[0])" in src
    assert "lc::conv<string>::from(c[1])" in src
    assert '#line 1 "solution.cpp"' in src


def test_cpp_two_sum(run):
    code = """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> d;
        for (int i = 0; i < nums.size(); ++i) {
            if (d.count(target - nums[i])) return {d[target - nums[i]], i};
            d[nums[i]] = i;
        }
        return {};
    }
};"""
    r = run(
        "cpp",
        code,
        "twoSum",
        [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}],
        [[[2, 7, 11, 15], 9], [[3, 3], 6]],
        cpp_sig=sig("twoSum", "vector<int>", ("vector<int>&", "nums"), ("int", "target")),
    )
    assert r["compile_error"] is None, r
    assert [x["value"] for x in r["results"]] == [[0, 1], [0, 1]]


def test_cpp_merge_intervals(run):
    code = """class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& iv) {
        sort(iv.begin(), iv.end());
        vector<vector<int>> out;
        for (auto& v : iv) {
            if (!out.empty() && out.back()[1] >= v[0]) out.back()[1] = max(out.back()[1], v[1]);
            else out.push_back(v);
        }
        return out;
    }
};"""
    r = run(
        "cpp",
        code,
        "merge",
        [{"name": "iv", "type": "List[List[int]]"}],
        [[[[1, 3], [2, 6], [8, 10]]]],
        cpp_sig=sig("merge", "vector<vector<int>>", ("vector<vector<int>>&", "iv")),
    )
    assert r["results"][0]["value"] == [[1, 6], [8, 10]]


def test_cpp_string_bool_char_double(run):
    code = """class Solution {
public:
    bool f(string s, vector<vector<char>>& g, long long n, double d) {
        return s.size() == 2 && g[1][0] == 'c' && n == 10000000000LL && d > 1.4;
    }
};"""
    r = run(
        "cpp",
        code,
        "f",
        [
            {"name": "s", "type": "str"},
            {"name": "g", "type": "List[List[str]]"},
            {"name": "n", "type": "int"},
            {"name": "d", "type": "float"},
        ],
        [["ab", [["a", "b"], ["c", "d"]], 10000000000, 1.5]],
        cpp_sig=sig("f", "bool", ("string", "s"), ("vector<vector<char>>&", "g"), ("long long", "n"), ("double", "d")),
    )
    assert r["results"][0]["value"] is True


def test_cpp_returns_char_and_string_vector(run):
    code = """class Solution {
public:
    char f(vector<string>& w) { return w[0][0]; }
};"""
    r = run(
        "cpp",
        code,
        "f",
        [{"name": "w", "type": "List[str]"}],
        [[["xy"]]],
        cpp_sig=sig("f", "char", ("vector<string>&", "w")),
    )
    assert r["results"][0]["value"] == "x"


def test_cpp_tree(run):
    code = """class Solution {
public:
    TreeNode* invert(TreeNode* root) {
        if (!root) return nullptr;
        swap(root->left, root->right);
        invert(root->left);
        invert(root->right);
        return root;
    }
};"""
    r = run(
        "cpp",
        code,
        "invert",
        [{"name": "root", "type": "TreeNode"}],
        [[[4, 2, 7, 1, 3]], [[]]],
        ret="TreeNode",
        cpp_sig=sig("invert", "TreeNode*", ("TreeNode*", "root")),
    )
    assert [x["value"] for x in r["results"]] == [[4, 7, 2, None, None, 3, 1], []]


def test_cpp_linked_list(run):
    code = """class Solution {
public:
    ListNode* rev(ListNode* head) {
        ListNode* prev = nullptr;
        while (head) { auto n = head->next; head->next = prev; prev = head; head = n; }
        return prev;
    }
};"""
    r = run(
        "cpp",
        code,
        "rev",
        [{"name": "head", "type": "ListNode"}],
        [[[1, 2, 3]], [[]]],
        ret="ListNode",
        cpp_sig=sig("rev", "ListNode*", ("ListNode*", "head")),
    )
    assert [x["value"] for x in r["results"]] == [[3, 2, 1], []]


def test_cpp_compile_error(run):
    r = run(
        "cpp",
        "class Solution {\npublic:\n    int f(int x) { return y; }\n};",
        "f",
        [{"name": "x", "type": "int"}],
        [[1]],
        cpp_sig=sig("f", "int", ("int", "x")),
    )
    assert "solution.cpp:3" in r["compile_error"]
    assert "error" in r["compile_error"]


def test_cpp_stdout_is_captured_per_case(run):
    code = 'class Solution {\npublic:\n    int f(int x) { cout << "saw " << x << endl; return x * 2; }\n};'
    r = run("cpp", code, "f", [{"name": "x", "type": "int"}], [[1], [2]], cpp_sig=sig("f", "int", ("int", "x")))
    assert [x["stdout"] for x in r["results"]] == ["saw 1\n", "saw 2\n"]
    assert [x["value"] for x in r["results"]] == [2, 4]


def test_cpp_exception_is_runtime_error(run):
    code = "class Solution {\npublic:\n    int f(vector<int>& a) { return a.at(5); }\n};"
    r = run(
        "cpp", code, "f", [{"name": "a", "type": "List[int]"}], [[[1]]], cpp_sig=sig("f", "int", ("vector<int>&", "a"))
    )
    assert r["results"][0]["ok"] is False
    assert "out_of_range" in r["results"][0]["error"]


def test_cpp_segfault_is_runtime_error(run):
    code = "class Solution {\npublic:\n    int f(int x) { int* p = nullptr; return *p + x; }\n};"
    r = run("cpp", code, "f", [{"name": "x", "type": "int"}], [[1]], cpp_sig=sig("f", "int", ("int", "x")))
    assert r["results"] == []
    assert r["exit_code"] == -11
    assert r["timed_out"] is False


@pytest.mark.parametrize(
    "lang,code,cpp",
    [
        (
            "python",
            "class Solution:\n    def __init__(self):\n        self.n = 0\n    def f(self, x: int) -> int:\n        self.n += 1\n        return self.n\n",
            None,
        ),
        ("java", "class Solution { int n = 0; public int f(int x) { return ++n; } }", None),
        (
            "cpp",
            "class Solution {\n    int n = 0;\npublic:\n    int f(int x) { return ++n; }\n};",
            sig("f", "int", ("int", "x")),
        ),
    ],
)
def test_fresh_solution_per_case(run, lang, code, cpp):
    r = run(lang, code, "f", [{"name": "x", "type": "int"}], [[1], [1]], cpp_sig=cpp)
    assert [x["value"] for x in r["results"]] == [1, 1]


def test_cpp_printf_is_captured_per_case(run):
    code = 'class Solution {\npublic:\n    int f(int x) { printf("p%d\\n", x); puts("q"); cout << "c" << x << "\\n"; return x; }\n};'
    r = run("cpp", code, "f", [{"name": "x", "type": "int"}], [[1], [2]], cpp_sig=sig("f", "int", ("int", "x")))
    assert [x["stdout"] for x in r["results"]] == ["p1\nq\nc1\n", "p2\nq\nc2\n"]
