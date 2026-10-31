"""Answer checkers: strings."""

from collections import Counter
from itertools import groupby, pairwise
from string import ascii_lowercase
from typing import Any

from localcode.judging.checkers import checker

LOWERCASE = frozenset(ascii_lowercase)
PARENS = frozenset("()")


def _repeats(s: str, run: int) -> bool:
    """Whether `s` has `run` equal characters in a row."""
    return any(len(list(g)) >= run for _, g in groupby(s))


def _is_subsequence(sub: list[Any] | str, seq: list[Any] | str) -> bool:
    it = iter(seq)
    return all(any(x == y for y in it) for x in sub)


def _subsequence_indices(sub: list[Any], seq: list[Any]) -> list[int] | None:
    """Indices of the earliest embedding of `sub` in `seq`, or None if it is not a subsequence."""
    indices, i = [], 0
    for x in sub:
        while i < len(seq) and seq[i] != x:
            i += 1
        if i == len(seq):
            return None
        indices.append(i)
        i += 1
    return indices


@checker("custom-sort-string")
def custom_sort_string(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of `s` whose characters from `order` appear in `order`'s order."""
    order, s = args
    rank = {c: i for i, c in enumerate(order)}
    ranks = [rank[c] for c in actual if c in rank]
    return isinstance(actual, str) and Counter(actual) == Counter(s) and all(x <= y for x, y in pairwise(ranks))


@checker("find-unique-binary-string")
def find_unique_binary_string(args: list[Any], expected: Any, actual: Any) -> bool:
    """A binary string of length n that is not in `nums`."""
    (nums,) = args
    return isinstance(actual, str) and len(actual) == len(nums) and set(actual) <= {"0", "1"} and actual not in nums


@checker("generate-a-string-with-characters-that-have-odd-counts")
def odd_counts(args: list[Any], expected: Any, actual: Any) -> bool:
    """`n` lowercase letters, each occurring an odd number of times."""
    (n,) = args
    return (
        isinstance(actual, str)
        and len(actual) == n
        and set(actual) <= LOWERCASE
        and all(k % 2 for k in Counter(actual).values())
    )


@checker("longest-happy-string")
def longest_happy_string(args: list[Any], expected: Any, actual: Any) -> bool:
    """An optimal-length string of at most a 'a', b 'b', c 'c', with no three equal letters in a row."""
    counts = Counter(actual)
    return (
        isinstance(actual, str)
        and len(actual) == len(expected)
        and set(actual) <= set("abc")
        and all(counts[ch] <= limit for ch, limit in zip("abc", args, strict=True))
        and not _repeats(actual, 3)
    )


@checker("minimum-remove-to-make-valid-parentheses")
def minimum_remove_parentheses(args: list[Any], expected: Any, actual: Any) -> bool:
    """A balanced subsequence of `s` that keeps every letter and has the optimal length."""
    (s,) = args
    if not isinstance(actual, str) or len(actual) != len(expected) or not _is_subsequence(actual, s):
        return False
    if [c for c in actual if c not in PARENS] != [c for c in s if c not in PARENS]:
        return False
    depth = 0
    for c in actual:
        depth += (c == "(") - (c == ")")
        if depth < 0:
            return False
    return depth == 0


@checker("reorganize-string")
def reorganize_string(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of `s` with no two equal adjacent characters, or "" when none exists."""
    (s,) = args
    if expected == "":
        return actual == ""
    return isinstance(actual, str) and Counter(actual) == Counter(s) and not _repeats(actual, 2)


@checker("replace-all-s-to-avoid-consecutive-repeating-characters")
def replace_question_marks(args: list[Any], expected: Any, actual: Any) -> bool:
    """`s` with each '?' replaced by a lowercase letter and no two equal adjacent characters."""
    (s,) = args
    return (
        isinstance(actual, str)
        and len(actual) == len(s)
        and set(actual) <= LOWERCASE
        and all(o == "?" or o == a for o, a in zip(s, actual, strict=True))
        and not _repeats(actual, 2)
    )


@checker("sort-characters-by-frequency")
def sort_by_frequency(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of `s` with each character's copies together, in non-increasing order of frequency."""
    (s,) = args
    if not isinstance(actual, str) or Counter(actual) != Counter(s):
        return False
    runs = [len(list(g)) for _, g in groupby(actual)]
    return len(runs) == len(set(actual)) and all(x >= y for x, y in pairwise(runs))


@checker("string-without-aaa-or-bbb")
def string_without_aaa_or_bbb(args: list[Any], expected: Any, actual: Any) -> bool:
    """Exactly a 'a' and b 'b' letters, with no three equal letters in a row."""
    a, b = args
    return (
        isinstance(actual, str)
        and len(actual) == a + b
        and actual.count("a") == a
        and actual.count("b") == b
        and not _repeats(actual, 3)
    )


@checker("longest-duplicate-substring")
def longest_duplicate_substring(args: list[Any], expected: Any, actual: Any) -> bool:
    """A substring of the optimal length that occurs at least twice in `s` (or "" when none exists)."""
    (s,) = args
    if expected == "":
        return actual == ""
    if not isinstance(actual, str) or not actual or len(actual) != len(expected):
        return False
    first = s.find(actual)
    return first >= 0 and s.find(actual, first + 1) >= 0


@checker("longest-unequal-adjacent-groups-subsequence-i")
def unequal_adjacent_groups_i(args: list[Any], expected: Any, actual: Any) -> bool:
    """An optimal-length subsequence of `words` whose adjacent elements have different groups."""
    words, groups = args
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    indices = _subsequence_indices(actual, words)
    return indices is not None and all(groups[i] != groups[j] for i, j in pairwise(indices))


def _hamming_one(x: str, y: str) -> bool:
    return len(x) == len(y) and sum(a != b for a, b in zip(x, y, strict=True)) == 1


@checker("longest-unequal-adjacent-groups-subsequence-ii")
def unequal_adjacent_groups_ii(args: list[Any], expected: Any, actual: Any) -> bool:
    """An optimal-length subsequence of `words` whose neighbours differ in group and are at Hamming distance 1."""
    words, groups = args
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    indices = _subsequence_indices(actual, words)
    return indices is not None and all(
        groups[i] != groups[j] and _hamming_one(words[i], words[j]) for i, j in pairwise(indices)
    )
