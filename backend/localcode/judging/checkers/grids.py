"""Answer checkers: grids."""

from collections import Counter
from itertools import pairwise
from typing import Any

from localcode.judging.checkers import checker


def _is_int(x: Any) -> bool:
    return type(x) is int


def _int_matrix(m: Any, rows: int, cols: int) -> bool:
    return (
        isinstance(m, list)
        and len(m) == rows
        and all(isinstance(r, list) and len(r) == cols and all(_is_int(x) for x in r) for r in m)
    )


@checker("build-a-matrix-with-conditions")
def build_matrix(args: list[Any], expected: Any, actual: Any) -> bool:
    """A k x k matrix holding 1..k once each (zeros elsewhere) meeting every row and column condition, or []."""
    k, row_conditions, col_conditions = args
    if expected == []:
        return actual == []
    if not _int_matrix(actual, k, k):
        return False
    row: dict[int, int] = {}
    col: dict[int, int] = {}
    for r, line in enumerate(actual):
        for c, v in enumerate(line):
            if v == 0:
                continue
            if not 1 <= v <= k or v in row:
                return False
            row[v], col[v] = r, c
    return (
        len(row) == k
        and all(row[a] < row[b] for a, b in row_conditions)
        and all(col[a] < col[b] for a, b in col_conditions)
    )


def _triangle_neighbors(i: int, j: int, n: int) -> list[tuple[int, int]]:
    out = [(i, j - 1)] if j > 1 else []
    if j < 2 * i - 1:
        out.append((i, j + 1))
    if j % 2 == 1 and i < n:
        out.append((i + 1, j + 1))
    elif j % 2 == 0:
        out.append((i - 1, j - 1))
    return out


@checker("color-the-triangle-red")
def color_red(args: list[Any], expected: Any, actual: Any) -> bool:
    """Distinct valid triangles, as few as the expected answer, whose spread turns every triangle red."""
    (n,) = args
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    # red_hits[(i - 1) ** 2 + j - 1] counts red neighbours; 2 or more means the triangle is red.
    red_hits = bytearray(n * n)
    stack: list[tuple[int, int]] = []
    for cell in actual:
        if not (isinstance(cell, list) and len(cell) == 2 and all(_is_int(x) for x in cell)):
            return False
        i, j = cell
        if not (1 <= i <= n and 1 <= j <= 2 * i - 1) or red_hits[(i - 1) ** 2 + j - 1]:
            return False
        red_hits[(i - 1) ** 2 + j - 1] = 2
        stack.append((i, j))
    red = len(stack)
    while stack:
        for i, j in _triangle_neighbors(*stack.pop(), n):
            idx = (i - 1) ** 2 + j - 1
            if red_hits[idx] < 2:
                red_hits[idx] += 1
                if red_hits[idx] == 2:
                    red += 1
                    stack.append((i, j))
    return red == n * n


@checker("construct-2d-grid-matching-graph-layout")
def construct_grid_layout(args: list[Any], expected: Any, actual: Any) -> bool:
    """A rectangular grid holding 0..n-1 once each where cells are adjacent exactly when their nodes share an edge."""
    n, edges = args
    if not isinstance(actual, list) or not actual or not isinstance(actual[0], list) or not actual[0]:
        return False
    rows, cols = len(actual), len(actual[0])
    if rows * cols != n or not _int_matrix(actual, rows, cols):
        return False
    if sorted(v for line in actual for v in line) != list(range(n)):
        return False
    edge_set = {(min(u, v), max(u, v)) for u, v in edges}
    adjacent = 0
    for r in range(rows):
        for c in range(cols):
            a = actual[r][c]
            for rr, cc in ((r + 1, c), (r, c + 1)):
                if rr < rows and cc < cols:
                    b = actual[rr][cc]
                    if (min(a, b), max(a, b)) not in edge_set:
                        return False
                    adjacent += 1
    return adjacent == len(edge_set)


@checker("convert-an-array-into-a-2d-array-with-conditions")
def convert_to_2d(args: list[Any], expected: Any, actual: Any) -> bool:
    """Rows of distinct values that together are exactly nums, with the minimal (expected) row count."""
    (nums,) = args
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    seen: Counter[int] = Counter()
    for line in actual:
        if not isinstance(line, list) or not all(_is_int(x) for x in line) or len(set(line)) != len(line):
            return False
        seen.update(line)
    return seen == Counter(nums)


@checker("divide-array-into-arrays-with-max-difference")
def divide_array(args: list[Any], expected: Any, actual: Any) -> bool:
    """Triples that together are exactly nums, each spanning at most k, or [] when impossible."""
    nums, k = args
    if expected == []:
        return actual == []
    if not isinstance(actual, list) or len(actual) * 3 != len(nums):
        return False
    seen: Counter[int] = Counter()
    for group in actual:
        if not (isinstance(group, list) and len(group) == 3 and all(_is_int(x) for x in group)):
            return False
        if max(group) - min(group) > k:
            return False
        seen.update(group)
    return seen == Counter(nums)


@checker("map-of-highest-peak")
def highest_peak(args: list[Any], expected: Any, actual: Any) -> bool:
    """Non-negative heights, 0 on water, neighbours differing by at most 1, with the maximal (expected) peak."""
    (is_water,) = args
    rows, cols = len(is_water), len(is_water[0])
    if not _int_matrix(actual, rows, cols):
        return False
    for r in range(rows):
        for c in range(cols):
            h = actual[r][c]
            if h < 0 or (is_water[r][c] and h != 0):
                return False
            if r + 1 < rows and abs(h - actual[r + 1][c]) > 1:
                return False
            if c + 1 < cols and abs(h - actual[r][c + 1]) > 1:
                return False
    return max(map(max, actual)) == max(map(max, expected))


def _keeps_order(original: list[int], replaced: list[int]) -> bool:
    ranked = [v for _, v in sorted(zip(original, replaced, strict=True))]
    return all(a < b for a, b in pairwise(ranked))


@checker("minimize-maximum-value-in-a-grid")
def minimize_grid_max(args: list[Any], expected: Any, actual: Any) -> bool:
    """Positive values keeping every row's and column's relative order, with the minimal (expected) maximum."""
    (grid,) = args
    rows, cols = len(grid), len(grid[0])
    if not _int_matrix(actual, rows, cols) or any(v < 1 for line in actual for v in line):
        return False
    if not all(_keeps_order(g, a) for g, a in zip(grid, actual, strict=True)):
        return False
    for c in range(cols):
        if not _keeps_order([line[c] for line in grid], [line[c] for line in actual]):
            return False
    return max(map(max, actual)) == max(map(max, expected))


@checker("reconstruct-a-2-row-binary-matrix")
def reconstruct_two_rows(args: list[Any], expected: Any, actual: Any) -> bool:
    """A 2 x n binary matrix with the given row sums and column sums, or [] when none exists."""
    upper, lower, colsum = args
    if expected == []:
        return actual == []
    if not _int_matrix(actual, 2, len(colsum)) or any(v not in (0, 1) for line in actual for v in line):
        return False
    top, bottom = actual
    return (
        sum(top) == upper
        and sum(bottom) == lower
        and all(a + b == s for a, b, s in zip(top, bottom, colsum, strict=True))
    )


@checker("matrix-cells-in-distance-order")
def cells_by_distance(args: list[Any], expected: Any, actual: Any) -> bool:
    """Every cell exactly once, in non-decreasing Manhattan distance from the centre."""
    rows, cols, r_center, c_center = args
    if not isinstance(actual, list) or len(actual) != rows * cols:
        return False
    seen: set[tuple[int, int]] = set()
    last = 0
    for cell in actual:
        if not (isinstance(cell, list) and len(cell) == 2 and all(_is_int(x) for x in cell)):
            return False
        r, c = cell
        if not (0 <= r < rows and 0 <= c < cols) or (r, c) in seen:
            return False
        seen.add((r, c))
        dist = abs(r - r_center) + abs(c - c_center)
        if dist < last:
            return False
        last = dist
    return True


@checker("find-a-good-subset-of-the-matrix")
def good_subset(args: list[Any], expected: Any, actual: Any) -> bool:
    """Ascending distinct row indices of a non-empty subset whose column sums are at most half its size, or []."""
    (grid,) = args
    if expected == []:
        return actual == []
    if not isinstance(actual, list) or not actual or not all(_is_int(i) for i in actual):
        return False
    if not all(a < b for a, b in pairwise(actual)) or not 0 <= actual[0] <= actual[-1] < len(grid):
        return False
    limit = len(actual) // 2
    return all(sum(grid[i][c] for i in actual) <= limit for c in range(len(grid[0])))
