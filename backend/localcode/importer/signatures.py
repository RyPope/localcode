"""Extract method signatures from Java/C++ reference code and render starter code (incl. Kotlin)."""

import re

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_TYPE = r"(?:(?:unsigned|signed|long|short|const)\s+)*[\w:]+(?:\s*<[\w\s,<>:*&\[\]]*>)?(?:\s*\[\s*\])*\s*[*&]*"
_JAVA_METHOD = re.compile(r"public\s+(?:static\s+)?(" + _TYPE + r")\s+(\w+)\s*\(([^)]*)\)\s*(?:throws [\w, ]+)?\{")
_CPP_METHOD = re.compile(
    r"(?:^|\n)\s*(?:virtual\s+|static\s+|inline\s+)*(" + _TYPE + r")\s*\b(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?\{"
)


def _strip_comments(src: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", src))


def _split_top(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        depth += ch == "<"
        depth -= ch == ">"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return [p.strip() for p in [*parts, cur] if p.strip()]


def _norm(t: str) -> str:
    t = re.sub(r"\s+", " ", t.strip())
    t = re.sub(r"\s*([<>,\[\]*&])\s*", r"\1", t)
    return t.replace(",", ", ")


def _params(s: str) -> list[dict]:
    out = []
    for p in _split_top(s):
        p = re.sub(r"^final\s+", "", p)
        m = re.match(r"(.*?)([\w]+)\s*$", p, re.S)
        if not m:
            raise ValueError(f"bad param {p!r}")
        out.append({"type": _norm(m.group(1)), "name": m.group(2)})
    return out


def _class_body(src: str, name: str = "Solution") -> str:
    m = re.search(r"\bclass\s+" + name + r"\b[^{]*\{", src)
    if not m:
        raise ValueError("no class Solution")
    return src[m.end() :]


def parse_java_sig(src: str) -> dict:
    body = _class_body(_strip_comments(src))
    m = _JAVA_METHOD.search(body)
    if not m:
        raise ValueError("no public method")
    return {"method": m.group(2), "ret": _norm(m.group(1)), "params": _params(m.group(3))}


def parse_cpp_sig(src: str) -> dict:
    body = _class_body(_strip_comments(src))
    pub = body.find("public:")
    if pub == -1:
        raise ValueError("no public section")
    m = _CPP_METHOD.search(body[pub + len("public:") :])
    if not m:
        raise ValueError("no public method")
    return {"method": m.group(2), "ret": _norm(m.group(1)), "params": _params(m.group(3))}


_JAVA_LIST_NODE = """/**
 * Definition for singly-linked list.
 * public class ListNode {
 *     int val;
 *     ListNode next;
 *     ListNode() {}
 *     ListNode(int val) { this.val = val; }
 *     ListNode(int val, ListNode next) { this.val = val; this.next = next; }
 * }
 */
"""
_JAVA_TREE_NODE = """/**
 * Definition for a binary tree node.
 * public class TreeNode {
 *     int val;
 *     TreeNode left;
 *     TreeNode right;
 *     TreeNode() {}
 *     TreeNode(int val) { this.val = val; }
 *     TreeNode(int val, TreeNode left, TreeNode right) {
 *         this.val = val;
 *         this.left = left;
 *         this.right = right;
 *     }
 * }
 */
"""
_CPP_LIST_NODE = """/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode() : val(0), next(nullptr) {}
 *     ListNode(int x) : val(x), next(nullptr) {}
 *     ListNode(int x, ListNode *next) : val(x), next(next) {}
 * };
 */
"""
_CPP_TREE_NODE = """/**
 * Definition for a binary tree node.
 * struct TreeNode {
 *     int val;
 *     TreeNode *left;
 *     TreeNode *right;
 *     TreeNode() : val(0), left(nullptr), right(nullptr) {}
 *     TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
 *     TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
 * };
 */
"""
_KT_LIST_NODE = """/**
 * Example:
 * var li = ListNode(5)
 * var v = li.`val`
 * Definition for singly-linked list.
 * class ListNode(var `val`: Int) {
 *     var next: ListNode? = null
 * }
 */
"""
_KT_TREE_NODE = """/**
 * Example:
 * var ti = TreeNode(5)
 * var v = ti.`val`
 * Definition for a binary tree node.
 * class TreeNode(var `val`: Int) {
 *     var left: TreeNode? = null
 *     var right: TreeNode? = null
 * }
 */
"""


def _node_header(sig: dict, list_hdr: str, tree_hdr: str) -> str:
    types = " ".join([sig["ret"]] + [p["type"] for p in sig["params"]])
    return (list_hdr if "ListNode" in types else "") + (tree_hdr if "TreeNode" in types else "")


def java_starter(sig: dict) -> str:
    params = ", ".join(f"{p['type']} {p['name']}" for p in sig["params"])
    return (
        _node_header(sig, _JAVA_LIST_NODE, _JAVA_TREE_NODE)
        + f"class Solution {{\n    public {sig['ret']} {sig['method']}({params}) {{\n        \n    }}\n}}\n"
    )


def cpp_starter(sig: dict) -> str:
    params = ", ".join(f"{p['type']} {p['name']}" for p in sig["params"])
    return (
        _node_header(sig, _CPP_LIST_NODE, _CPP_TREE_NODE)
        + f"class Solution {{\npublic:\n    {sig['ret']} {sig['method']}({params}) {{\n        \n    }}\n}};\n"
    )


_KT_PRIM = {
    "int": "Int",
    "long": "Long",
    "double": "Double",
    "float": "Float",
    "boolean": "Boolean",
    "char": "Char",
    "String": "String",
    "Integer": "Int",
    "Long": "Long",
    "Double": "Double",
    "Boolean": "Boolean",
    "Character": "Char",
    "void": "Unit",
    "ListNode": "ListNode?",
    "TreeNode": "TreeNode?",
}
_KT_PRIM_ARRAY = {
    "int": "IntArray",
    "long": "LongArray",
    "double": "DoubleArray",
    "boolean": "BooleanArray",
    "char": "CharArray",
    "float": "FloatArray",
}


def kotlin_type(t: str) -> str:
    t = t.strip()
    if t.endswith("[]"):
        inner = t[:-2]
        if inner in _KT_PRIM_ARRAY:
            return _KT_PRIM_ARRAY[inner]
        return f"Array<{kotlin_type(inner)}>"
    m = re.fullmatch(r"(\w+)<(.*)>", t)
    if m:
        return f"{m.group(1)}<{', '.join(kotlin_type(a) for a in _split_top(m.group(2)))}>"
    if t in _KT_PRIM:
        return _KT_PRIM[t]
    raise ValueError(f"no Kotlin mapping for {t!r}")


def kotlin_starter(java_sig: dict) -> str:
    params = ", ".join(f"{p['name']}: {kotlin_type(p['type'])}" for p in java_sig["params"])
    ret = kotlin_type(java_sig["ret"])
    return (
        _node_header(java_sig, _KT_LIST_NODE, _KT_TREE_NODE)
        + f"class Solution {{\n    fun {java_sig['method']}({params}): {ret} {{\n        \n    }}\n}}\n"
    )
