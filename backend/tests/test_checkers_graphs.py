from typing import Any

import pytest

from localcode.judging.compare import judge

# slug, args, expected (the statement's answer), other valid answers, invalid answers
CASES: list[tuple[str, list[Any], Any, list[Any], list[Any]]] = [
    (
        "avoid-flood-in-the-city",
        [[1, 2, 0, 0, 2, 1]],
        [-1, -1, 2, 1, -1, -1],
        [[-1, -1, 1, 2, -1, -1]],
        [[-1, -1, 2, 2, -1, -1], [-1, -1, 0, 1, -1, -1], [-1, -1, 2, 1, -1], [], [-1, -1, 2.0, 1, -1, -1]],
    ),
    ("avoid-flood-in-the-city", [[1, 2, 0, 1, 2]], [], [], [[-1, -1, 1, -1, -1], [-1, -1, 2, -1, -1]]),
    (
        "avoid-flood-in-the-city",
        [[1, 0, 2, 0, 1]],
        [-1, 1, -1, 5, -1],
        [[-1, 9, -1, 1, -1]],
        [[-1, 2, -1, 2, -1], [-1, 1, -1, 1_000_000_001, -1]],
    ),
    (
        "balance-a-binary-search-tree",
        [[1, None, 2, None, 3, None, 4, None, None]],
        [2, 1, 3, None, None, None, 4],
        [[3, 1, 4, None, 2], [2, 1, 4, None, None, 3], [3, 2, 4, 1]],
        [
            [1, None, 2, None, 3, None, 4],
            [2, 1, 3],
            [2, 1, 3, None, None, None, 5],
            [3, 1, 4, 2],
            [3, 1, 4, None, 2, None],
        ],
    ),
    (
        "construct-binary-tree-from-preorder-and-postorder-traversal",
        [[1, 2, 4, 5, 3, 6, 7], [4, 5, 2, 6, 7, 3, 1]],
        [1, 2, 3, 4, 5, 6, 7],
        [],
        [[1, 3, 2, 6, 7, 4, 5], [1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6, 7, None]],
    ),
    (
        "construct-binary-tree-from-preorder-and-postorder-traversal",
        [[1, 2, 3], [3, 2, 1]],
        [1, 2, None, 3],
        [[1, None, 2, None, 3], [1, 2, None, None, 3], [1, None, 2, 3]],
        [[1, 2, 3], [1, 3, None, 2], [None, 1, 2, None, 3]],
    ),
    (
        "course-schedule-ii",
        [4, [[1, 0], [2, 0], [3, 1], [3, 2]]],
        [0, 2, 1, 3],
        [[0, 1, 2, 3]],
        [[0, 1, 3, 2], [0, 1, 2], [0, 1, 1, 3], [], [0, 1, 2, 4]],
    ),
    ("course-schedule-ii", [2, [[1, 0], [0, 1]]], [], [], [[0, 1], [1, 0]]),
    (
        "flower-planting-with-no-adjacent",
        [3, [[1, 2], [2, 3], [3, 1]]],
        [1, 2, 3],
        [[1, 2, 4], [1, 4, 2], [3, 2, 1]],
        [[1, 2, 1], [1, 2, 5], [0, 1, 2], [1, 2]],
    ),
    (
        "insert-into-a-binary-search-tree",
        [[4, 2, 7, 1, 3], 5],
        [4, 2, 7, 1, 3, 5],
        [[5, 2, 7, 1, 3, None, None, None, None, None, 4], [3, 2, 5, 1, None, 4, 7]],
        [[4, 2, 7, 1, 3, None, 5], [4, 2, 7, 1, 3], [4, 2, 7, 1, 3, 5, None], [4, 2, 7, 1, 3, 6]],
    ),
    ("insert-into-a-binary-search-tree", [[], 5], [5], [], [[], [5, None], [5, 5]]),
    (
        "modify-graph-edge-weights",
        [5, [[4, 1, -1], [2, 0, -1], [0, 3, -1], [4, 3, -1]], 0, 1, 5],
        [[4, 1, 1], [2, 0, 1], [0, 3, 3], [4, 3, 1]],
        [[[0, 3, 1], [1, 4, 3], [2, 0, 2000000000], [4, 3, 1]]],
        [
            [[4, 1, 1], [2, 0, 1], [0, 3, 1], [4, 3, 1]],
            [[4, 1, 1], [2, 0, 0], [0, 3, 3], [4, 3, 1]],
            [[4, 1, 1], [0, 3, 3], [4, 3, 1]],
            [[4, 1, 1], [2, 0, 1], [0, 3, 3], [4, 3, 1], [4, 3, 1]],
            [[4, 1, 1], [2, 1, 1], [0, 3, 3], [4, 3, 1]],
            [],
        ],
    ),
    (
        "modify-graph-edge-weights",
        [4, [[1, 0, 4], [1, 2, 3], [2, 3, 5], [0, 3, -1]], 0, 2, 6],
        [[1, 0, 4], [1, 2, 3], [2, 3, 5], [0, 3, 1]],
        [],
        [[[1, 0, 4], [1, 2, 3], [2, 3, 5], [0, 3, 2]], [[1, 0, 5], [1, 2, 2], [2, 3, 5], [0, 3, 1]]],
    ),
    ("modify-graph-edge-weights", [3, [[0, 1, -1], [0, 2, 5]], 0, 2, 6], [], [], [[[0, 1, 1], [0, 2, 5]]]),
    (
        "remove-zero-sum-consecutive-nodes-from-linked-list",
        [[1, 2, -3, 3, 1]],
        [3, 1],
        [[1, 2, 1]],
        [[1, 2, -3, 3, 1], [1], [1, 3], [3, 1, 0], []],
    ),
    (
        "remove-zero-sum-consecutive-nodes-from-linked-list",
        [[1, 2, 3, -3, -2]],
        [1],
        [],
        [[1, 2, -2], [1, 2], [2, -2, 1]],
    ),
    (
        "remove-zero-sum-consecutive-nodes-from-linked-list",
        [[2, 5, -5, -2, 2, 7]],
        [2, 7],
        [],
        [[7], [2, 2, 7], [5, 7]],
    ),
    (
        "restore-the-array-from-adjacent-pairs",
        [[[4, -2], [1, 4], [-3, 1]]],
        [-2, 4, 1, -3],
        [[-3, 1, 4, -2]],
        [[-2, 4, 1], [-2, 1, 4, -3], [-2, 4, 1, -3, -2], [4, -2, 1, -3]],
    ),
    (
        "sort-items-by-groups-respecting-dependencies",
        [8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3, 6], [], [], []]],
        [6, 3, 4, 1, 5, 2, 0, 7],
        [[6, 3, 4, 5, 2, 0, 7, 1], [0, 7, 5, 2, 6, 3, 4, 1]],
        [[3, 6, 4, 1, 5, 2, 0, 7], [6, 3, 1, 4, 5, 2, 0, 7], [6, 3, 4, 1, 5, 2, 0], [], [6, 3, 4, 1, 5, 2, 0, 0]],
    ),
    (
        "sort-items-by-groups-respecting-dependencies",
        [8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3], [], [4], []]],
        [],
        [],
        [[6, 3, 4, 1, 5, 2, 0, 7], [0, 1, 2, 3, 4, 5, 6, 7]],
    ),
    (
        "the-most-similar-path-in-a-graph",
        [
            5,
            [[0, 2], [0, 3], [1, 2], [1, 3], [1, 4], [2, 4]],
            ["ATL", "PEK", "LAX", "DXB", "HND"],
            ["ATL", "DXB", "HND", "LAX"],
        ],
        [0, 2, 4, 2],
        [[0, 3, 0, 2], [0, 3, 1, 2]],
        [[0, 3, 4, 2], [0, 2, 1, 2], [0, 2, 4], [0, 2, 4, 2, 0], [0, 2, 2, 2]],
    ),
    (
        "valid-arrangement-of-pairs",
        [[[1, 3], [3, 2], [2, 1]]],
        [[1, 3], [3, 2], [2, 1]],
        [[[2, 1], [1, 3], [3, 2]], [[3, 2], [2, 1], [1, 3]]],
        [[[1, 3], [2, 1], [3, 2]], [[1, 3], [3, 2]], [[1, 3], [3, 2], [2, 1], [1, 3]], [[1, 3], [3, 1], [1, 2]]],
    ),
    (
        "smallest-sufficient-team",
        [["java", "nodejs", "reactjs"], [["java"], ["nodejs"], ["nodejs", "reactjs"]]],
        [0, 2],
        [[2, 0]],
        [[0, 1, 2], [0, 1], [0, 0], [2, 3], [2]],
    ),
    (
        "smallest-sufficient-team",
        [["a", "b"], [["a"], ["b"], ["a", "b"], ["a", "b"]]],
        [2],
        [[3]],
        [[0, 1], [0], [True]],
    ),
    (
        "group-the-people-given-the-group-size-they-belong-to",
        [[3, 3, 3, 3, 3, 1, 3]],
        [[5], [0, 1, 2], [3, 4, 6]],
        [[[2, 1, 6], [5], [0, 4, 3]], [[5], [0, 6, 2], [4, 3, 1]]],
        [
            [[5], [0, 1, 2], [3, 4]],
            [[5], [0, 1, 2, 3], [4, 6]],
            [[5], [0, 1, 2], [3, 4, 6], []],
            [[5], [0, 1, 2], [3, 4, 4]],
        ],
    ),
]


@pytest.mark.parametrize(("slug", "args", "expected", "others", "invalid"), CASES, ids=[c[0] for c in CASES])
def test_graph_checkers(slug: str, args: list[Any], expected: Any, others: list[Any], invalid: list[Any]) -> None:
    mode = f"checker:{slug}"
    assert judge(expected, expected, mode, args)
    for answer in others:
        assert judge(expected, answer, mode, args), answer
    for answer in invalid:
        assert not judge(expected, answer, mode, args), answer


def test_every_slug_has_a_different_valid_answer() -> None:
    slugs = {c[0] for c in CASES}
    assert len(slugs) == 14
    assert slugs == {c[0] for c in CASES if c[3]}
