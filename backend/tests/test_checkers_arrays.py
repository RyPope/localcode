from typing import Any

import pytest

from localcode.judging.compare import judge

# (slug, args, expected, valid answers (statement example first), invalid answers)
CASES: list[tuple[str, list[Any], Any, list[Any], list[Any]]] = [
    (
        "advantage-shuffle",
        [[2, 7, 11, 15], [1, 10, 4, 11]],
        [2, 11, 7, 15],
        [[2, 11, 7, 15]],
        [[7, 11, 2, 15], [2, 11, 7], [2, 11, 7, 16], [2, 11, 7, 15, 1]],
    ),
    (
        "advantage-shuffle",
        [[5, 6, 7], [1, 1, 10]],
        [5, 6, 7],
        [[5, 6, 7], [7, 6, 5]],
        [[5, 7, 10], [5, 6], [5, 6, 8]],
    ),
    (
        "array-with-elements-not-equal-to-average-of-neighbors",
        [[1, 2, 3, 4, 5]],
        [1, 2, 4, 5, 3],
        [[1, 2, 4, 5, 3], [1, 3, 2, 5, 4]],
        [[1, 2, 3, 4, 5], [1, 2, 4, 5], [1, 2, 4, 5, 6]],
    ),
    (
        "distant-barcodes",
        [[1, 1, 1, 2, 2, 2]],
        [2, 1, 2, 1, 2, 1],
        [[2, 1, 2, 1, 2, 1], [1, 2, 1, 2, 1, 2]],
        [[1, 1, 2, 2, 1, 2], [1, 2, 1, 2, 1], [1, 2, 1, 2, 1, 3]],
    ),
    (
        "find-anagram-mappings",
        [[12, 28, 46, 32, 50, 12], [50, 12, 32, 46, 28, 12]],
        [1, 4, 3, 2, 0, 5],
        [[1, 4, 3, 2, 0, 5], [5, 4, 3, 2, 0, 1]],
        [[0, 4, 3, 2, 0, 5], [1, 4, 3, 2, 0], [1, 4, 3, 2, 0, 6], [1, 4, 3, 2, 0, -1]],
    ),
    (
        "find-indices-with-index-and-value-difference-i",
        [[5, 1, 4, 1], 2, 4],
        [0, 3],
        [[0, 3], [3, 0]],
        [[0, 2], [1, 3], [-1, -1], [0, 4], [0, 3, 1]],
    ),
    (
        "find-indices-with-index-and-value-difference-ii",
        [[2, 1], 0, 0],
        [0, 0],
        [[0, 0], [1, 0], [1, 1]],
        [[-1, -1], [0, 2], [0]],
    ),
    (
        "find-indices-with-index-and-value-difference-ii",
        [[1, 2, 3], 2, 4],
        [-1, -1],
        [[-1, -1]],
        [[0, 2], [-1]],
    ),
    (
        "find-subsequence-of-length-k-with-the-largest-sum",
        [[3, 4, 3, 3], 2],
        [3, 4],
        [[3, 4], [4, 3]],
        [[3, 3], [4, 4], [3, 4, 3], [5, 2]],
    ),
    (
        "sort-array-by-parity",
        [[3, 1, 2, 4]],
        [2, 4, 3, 1],
        [[2, 4, 3, 1], [4, 2, 1, 3]],
        [[2, 3, 4, 1], [2, 4, 3], [2, 4, 3, 5]],
    ),
    (
        "sort-array-by-parity-ii",
        [[4, 2, 5, 7]],
        [4, 5, 2, 7],
        [[4, 5, 2, 7], [2, 7, 4, 5]],
        [[4, 2, 5, 7], [4, 5, 2], [4, 5, 6, 7]],
    ),
    (
        "neither-minimum-nor-maximum",
        [[3, 2, 1, 4]],
        2,
        [2, 3],
        [1, 4, 5, -1, [2]],
    ),
    (
        "neither-minimum-nor-maximum",
        [[1, 2]],
        -1,
        [-1],
        [1, 2],
    ),
    (
        "subarray-with-elements-greater-than-varying-threshold",
        [[6, 5, 6, 5, 8], 7],
        1,
        [1, 2, 3, 4, 5],
        [0, 6, -1, True],
    ),
    (
        "subarray-with-elements-greater-than-varying-threshold",
        [[1, 3, 4, 3, 1], 6],
        3,
        [3],
        [1, 2, 4, -1],
    ),
    (
        "three-equal-parts",
        [[1, 0, 1, 0, 1]],
        [0, 3],
        [[0, 3]],
        [[0, 2], [1, 3], [-1, -1], [0, 5]],
    ),
    (
        "three-equal-parts",
        [[0, 0, 0, 0]],
        [0, 2],
        [[0, 2], [1, 3], [0, 3]],
        [[0, 1], [2, 4], [-1, -1]],
    ),
    (
        "three-equal-parts",
        [[1, 1, 0, 1, 1]],
        [-1, -1],
        [[-1, -1]],
        [[0, 2], [1, 3]],
    ),
    (
        "maximum-nesting-depth-of-two-valid-parentheses-strings",
        ["(()())"],
        [0, 1, 1, 1, 1, 0],
        [[0, 1, 1, 1, 1, 0], [1, 0, 0, 0, 0, 1]],
        [[0, 0, 0, 0, 0, 0], [0, 1, 0, 1, 1, 0], [0, 1, 1, 1, 1], [0, 1, 1, 1, 1, 2]],
    ),
    (
        "fair-candy-swap",
        [[1, 2], [2, 3]],
        [1, 2],
        [[1, 2], [2, 3]],
        [[2, 2], [1, 3], [3, 4], [1]],
    ),
]


@pytest.mark.parametrize(("slug", "args", "expected", "valid", "invalid"), CASES, ids=[c[0] for c in CASES])
def test_checker(slug: str, args: list[Any], expected: Any, valid: list[Any], invalid: list[Any]) -> None:
    mode = f"checker:{slug}"
    for answer in valid:
        assert judge(expected, answer, mode, args), f"{slug} rejected valid {answer}"
    for answer in invalid:
        assert not judge(expected, answer, mode, args), f"{slug} accepted invalid {answer}"
