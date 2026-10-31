from pathlib import Path

from localcode.importer.dataset import load_rows, params_from_starter, parse_cases, parse_examples

FIX = Path(__file__).parent / "fixtures" / "dataset_rows.jsonl"


def rows():
    return {p.slug: p for p in load_rows(FIX)}


def test_params_from_starter():
    method, params, ret = params_from_starter(
        "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        "
    )
    assert method == "twoSum"
    assert params == [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}]
    assert ret == "List[int]"


def test_optional_treenode_param():
    _, params, ret = params_from_starter(
        "class Solution:\n    def f(self, root: Optional[TreeNode], m: Dict[int, List[int]]) -> Optional[TreeNode]:\n"
    )
    assert params == [{"name": "root", "type": "TreeNode"}, {"name": "m", "type": "Dict[int, List[int]]"}]
    assert ret == "TreeNode"


def test_parse_cases_eq_positional_in_param_order():
    params = [{"name": "nums", "type": "List[int]"}, {"name": "goal", "type": "int"}]
    cases = parse_cases("def check(candidate):\n    assert candidate(goal = 10,nums = [5, 5]) == [0, 1]\n", params)
    assert cases == [{"args": [[5, 5], 10], "expected": [0, 1]}]


def test_parse_cases_tree():
    p = rows()["tree-mirror"]
    assert p.cases[0] == {"args": [[1, 2, 3]], "expected": [1, 3, 2]}
    assert p.cases[2] == {"args": [[]], "expected": []}


def test_parse_cases_list_node():
    p = rows()["list-reverse"]
    assert p.cases[0] == {"args": [[1, 2]], "expected": [2, 1]}
    assert p.cases[3] == {"args": [[]], "expected": []}


def test_parse_cases_skips_mismatched_names():
    params = [{"name": "nums", "type": "List[int]"}]
    assert parse_cases("def check(candidate):\n    assert candidate(other = 1) == 2\n", params) == []


def test_examples_from_description():
    p = rows()["pair-sum"]
    assert p.examples == [[[1, 4, 6], 10], [[5, 5], 10]]
    assert parse_examples("Input: root = [1,null,2]\nOutput: x", [{"name": "root", "type": "TreeNode"}]) == [
        [[1, None, 2]]
    ]


def test_any_order_mode_detected():
    assert rows()["tree-mirror"].compare_mode == "any_order"
    assert rows()["pair-sum"].compare_mode == "exact"


def test_none_return_has_no_tests():
    assert rows()["fill-in-place"].has_tests is False
    assert rows()["pair-sum"].has_tests is True


def test_ref_python_includes_header_and_completion():
    ref = rows()["pair-sum"].ref_python
    assert "class ListNode" in ref and "def pairSum" in ref


def test_params_skip_commented_node_definition():
    starter = (
        "# Definition for singly-linked list.\n# class ListNode:\n#     def __init__(self, val=0, next=None):\n"
        "#         self.val = val\nclass Solution:\n"
        "    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:\n        "
    )
    method, params, ret = params_from_starter(starter)
    assert method == "addTwoNumbers"
    assert [p["name"] for p in params] == ["l1", "l2"]
    assert ret == "ListNode"


def test_signature_skips_private_helpers():
    from localcode.importer.dataset import params_from_starter

    code = "class Solution:\n    def _h(self, x: int) -> int:\n        return x\n\n    def main(self, a: int, b: int) -> int:\n        return a\n"
    method, params, ret = params_from_starter(code)
    assert method == "main" and [p["name"] for p in params] == ["a", "b"]
