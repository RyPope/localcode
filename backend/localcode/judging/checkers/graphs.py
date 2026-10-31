"""Answer checkers: graphs, trees and linked lists."""

import heapq
from collections import Counter
from itertools import pairwise
from typing import Any

from localcode.judging.checkers import checker

# A parsed binary tree: node values, then left and right child indexes (-1 for no child). Nodes are
# numbered in level order, so every child's index is greater than its parent's.
Tree = tuple[list[int], list[int], list[int]]

MAX_LAKE = 10**9
MAX_EDGE_WEIGHT = 2 * 10**9


def _is_int(x: Any) -> bool:
    return type(x) is int


def _is_permutation(x: Any, n: int) -> bool:
    return isinstance(x, list) and len(x) == n and all(_is_int(v) and 0 <= v < n for v in x) and len(set(x)) == n


def _parse_tree(data: Any, *, strict: bool = True) -> Tree:
    """Parse a level-order array like the harness; `strict` (for answers) rejects trailing `None`s and unused values."""
    if not isinstance(data, list):
        raise TypeError("a tree must be a list")
    vals: list[int] = []
    left: list[int] = []
    right: list[int] = []
    if not data or data[0] is None:
        if strict and data:
            raise ValueError("a non-empty tree must start with its root")
        return vals, left, right
    if strict and data[-1] is None:
        raise ValueError("trailing None")

    def add(v: Any) -> int:
        if not _is_int(v):
            raise TypeError("tree values must be integers")
        vals.append(v)
        left.append(-1)
        right.append(-1)
        return len(vals) - 1

    add(data[0])
    i, q = 1, 0
    while q < len(vals) and i < len(data):
        for side in (left, right):
            if i < len(data) and data[i] is not None:
                side[q] = add(data[i])
            i += 1
        q += 1
    if strict and i < len(data):
        raise ValueError("values left over after the last node")
    return vals, left, right


def _inorder(t: Tree) -> list[int]:
    vals, left, right = t
    out: list[int] = []
    stack: list[int] = []
    node = 0 if vals else -1
    while stack or node != -1:
        while node != -1:
            stack.append(node)
            node = left[node]
        node = stack.pop()
        out.append(vals[node])
        node = right[node]
    return out


def _preorder(t: Tree, first: int = 0, second: int = 1) -> list[int]:
    """Root, then subtrees; `first`/`second` pick the child order (0 = left, 1 = right)."""
    vals, *children = t
    out: list[int] = []
    stack = [0] if vals else []
    while stack:
        node = stack.pop()
        out.append(vals[node])
        stack.extend(c for c in (children[second][node], children[first][node]) if c != -1)
    return out


def _postorder(t: Tree) -> list[int]:
    return _preorder(t, first=1, second=0)[::-1]


def _is_bst_of(t: Tree, values: list[int]) -> bool:
    order = _inorder(t)
    return all(a < b for a, b in pairwise(order)) and order == sorted(values)


def _is_balanced(t: Tree) -> bool:
    _, left, right = t
    height = [0] * len(left)
    for i in reversed(range(len(left))):
        hl = height[left[i]] if left[i] != -1 else 0
        hr = height[right[i]] if right[i] != -1 else 0
        if abs(hl - hr) > 1:
            return False
        height[i] = 1 + max(hl, hr)
    return True


def _shortest(adj: list[list[tuple[int, int]]], source: int, dest: int) -> float:
    dist = [float("inf")] * len(adj)
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == dest:
            return d
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (d + w, v))
    return dist[dest]


@checker("avoid-flood-in-the-city")
def avoid_flood(args: list[Any], expected: Any, actual: Any) -> bool:
    """-1 on rainy days, a lake in [1, 1e9] dried on dry days, no lake rained on twice while full; [] iff impossible."""
    rains = args[0]
    if expected == []:
        return actual == []
    if not isinstance(actual, list) or len(actual) != len(rains):
        return False
    full: set[int] = set()
    for lake, choice in zip(rains, actual, strict=True):
        if not _is_int(choice):
            return False
        if lake > 0:
            if choice != -1 or lake in full:
                return False
            full.add(lake)
        elif 1 <= choice <= MAX_LAKE:
            full.discard(choice)
        else:
            return False
    return True


@checker("balance-a-binary-search-tree")
def balance_bst(args: list[Any], expected: Any, actual: Any) -> bool:
    """A height-balanced BST holding exactly the input tree's values."""
    tree = _parse_tree(actual)
    return _is_bst_of(tree, _parse_tree(args[0], strict=False)[0]) and _is_balanced(tree)


@checker("construct-binary-tree-from-preorder-and-postorder-traversal")
def tree_from_pre_post(args: list[Any], expected: Any, actual: Any) -> bool:
    """A binary tree whose preorder and postorder traversals equal the given ones."""
    tree = _parse_tree(actual)
    return _preorder(tree) == args[0] and _postorder(tree) == args[1]


@checker("course-schedule-ii")
def course_order(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 0..n-1 taking every prerequisite first, or [] exactly when no order exists."""
    n, prerequisites = args
    if expected == []:
        return actual == []
    if not _is_permutation(actual, n):
        return False
    pos = {course: i for i, course in enumerate(actual)}
    return all(pos[b] < pos[a] for a, b in prerequisites)


@checker("flower-planting-with-no-adjacent")
def garden_colouring(args: list[Any], expected: Any, actual: Any) -> bool:
    """One flower type in 1..4 per garden, different across every path."""
    n, paths = args
    if not isinstance(actual, list) or len(actual) != n or not all(_is_int(f) and 1 <= f <= 4 for f in actual):
        return False
    return all(actual[x - 1] != actual[y - 1] for x, y in paths)


@checker("insert-into-a-binary-search-tree")
def insert_into_bst(args: list[Any], expected: Any, actual: Any) -> bool:
    """A BST holding exactly the original values plus `val`."""
    root, val = args
    return _is_bst_of(_parse_tree(actual), [*_parse_tree(root, strict=False)[0], val])


@checker("modify-graph-edge-weights")
def modify_edge_weights(args: list[Any], expected: Any, actual: Any) -> bool:
    """Every edge once, given weights kept, -1s set within [1, 2e9], shortest path == target; [] iff impossible."""
    n, edges, source, destination, target = args
    if expected == []:
        return actual == []
    if not isinstance(actual, list) or len(actual) != len(edges):
        return False
    given = {frozenset((a, b)): w for a, b, w in edges}
    seen: set[frozenset[int]] = set()
    adj: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for edge in actual:
        if not isinstance(edge, list) or len(edge) != 3 or not all(_is_int(v) for v in edge):
            return False
        a, b, w = edge
        key = frozenset((a, b))
        if key not in given or key in seen:
            return False
        fixed = given[key]
        if (fixed == -1 and not 1 <= w <= MAX_EDGE_WEIGHT) or (fixed != -1 and w != fixed):
            return False
        seen.add(key)
        adj[a].append((b, w))
        adj[b].append((a, w))
    return _shortest(adj, source, destination) == target


@checker("remove-zero-sum-consecutive-nodes-from-linked-list")
def remove_zero_sum(args: list[Any], expected: Any, actual: Any) -> bool:
    """The list left after deleting zero-sum runs: a subsequence whose dropped gaps sum to 0, with no zero-sum run."""
    head = args[0]
    if not isinstance(actual, list) or not all(_is_int(v) for v in actual):
        return False
    prefix, prefixes = 0, {0}
    for v in actual:
        prefix += v
        if prefix in prefixes:
            return False
        prefixes.add(prefix)
    if prefix != sum(head):
        return False
    matched = kept = dropped_before = 0
    for v in head:
        if matched < len(actual) and v == actual[matched] and dropped_before == kept:
            kept += v
            matched += 1
        dropped_before += v
    return matched == len(actual)


@checker("restore-the-array-from-adjacent-pairs")
def restore_from_pairs(args: list[Any], expected: Any, actual: Any) -> bool:
    """n distinct integers whose adjacent pairs are exactly the given pairs."""
    pairs = args[0]
    if not isinstance(actual, list) or len(actual) != len(pairs) + 1 or not all(_is_int(v) for v in actual):
        return False
    if len(set(actual)) != len(actual):
        return False
    return Counter(frozenset(p) for p in pairs) == Counter(frozenset(p) for p in pairwise(actual))


@checker("sort-items-by-groups-respecting-dependencies")
def sort_items_by_groups(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of the items with every group contiguous and every beforeItems entry earlier; [] iff impossible."""
    n, _, group, before_items = args
    if expected == []:
        return actual == []
    if not _is_permutation(actual, n):
        return False
    pos = [0] * n
    for i, item in enumerate(actual):
        pos[item] = i
    if any(pos[b] > pos[item] for item in range(n) for b in before_items[item]):
        return False
    spans: dict[int, list[int]] = {}
    for item, g in enumerate(group):
        if g != -1:
            lo, hi, count = spans.setdefault(g, [pos[item], pos[item], 0])
            spans[g] = [min(lo, pos[item]), max(hi, pos[item]), count + 1]
    return all(hi - lo + 1 == count for lo, hi, count in spans.values())


@checker("the-most-similar-path-in-a-graph")
def most_similar_path(args: list[Any], expected: Any, actual: Any) -> bool:
    """A path along roads, as long as targetPath, with the same (minimum) edit distance as the expected path."""
    n, roads, names, target_path = args
    if not isinstance(actual, list) or len(actual) != len(target_path):
        return False
    if not all(_is_int(c) and 0 <= c < n for c in actual):
        return False
    adjacent = {(a, b) for a, b in roads} | {(b, a) for a, b in roads}
    if not all(step in adjacent for step in pairwise(actual)):
        return False

    def distance(path: list[int]) -> int:
        return sum(names[c] != t for c, t in zip(path, target_path, strict=True))

    return distance(actual) == distance(expected)


@checker("valid-arrangement-of-pairs")
def valid_arrangement(args: list[Any], expected: Any, actual: Any) -> bool:
    """A reordering of the pairs where each pair starts where the previous one ends."""
    pairs = args[0]
    if not isinstance(actual, list) or len(actual) != len(pairs):
        return False
    if not all(isinstance(p, list) and len(p) == 2 and all(_is_int(v) for v in p) for p in actual):
        return False
    if Counter(map(tuple, actual)) != Counter(map(tuple, pairs)):
        return False
    return all(prev[1] == cur[0] for prev, cur in pairwise(actual))


@checker("smallest-sufficient-team")
def smallest_team(args: list[Any], expected: Any, actual: Any) -> bool:
    """Distinct people covering every required skill, as few as the expected team."""
    req_skills, people = args
    if not isinstance(actual, list) or len(actual) != len(expected) or len(set(actual)) != len(actual):
        return False
    if not all(_is_int(p) and 0 <= p < len(people) for p in actual):
        return False
    return set(req_skills) <= {skill for p in actual for skill in people[p]}


@checker("group-the-people-given-the-group-size-they-belong-to")
def group_people(args: list[Any], expected: Any, actual: Any) -> bool:
    """A partition of 0..n-1 into groups where each person's group has their stated size."""
    sizes = args[0]
    if not isinstance(actual, list):
        return False
    seen: set[int] = set()
    for members in actual:
        if not isinstance(members, list) or not members:
            return False
        for person in members:
            if not _is_int(person) or not 0 <= person < len(sizes) or person in seen or sizes[person] != len(members):
                return False
            seen.add(person)
    return len(seen) == len(sizes)
