"""Answer checkers: numbers."""

from collections import Counter
from itertools import pairwise
from typing import Any

from localcode.judging.checkers import checker

INT32_LIMIT = 2**31


def _ints(xs: Any) -> bool:
    return isinstance(xs, list) and all(type(x) is int for x in xs)


def _is_perm(xs: Any, lo: int, hi: int) -> bool:
    """Whether `xs` is a permutation of the integers in [lo, hi]."""
    return _ints(xs) and len(xs) == hi - lo + 1 and set(xs) == set(range(lo, hi + 1))


def _one_bit_apart(a: int, b: int) -> bool:
    return (a ^ b).bit_count() == 1


def _is_gray_cycle(xs: Any, n: int, start: int) -> bool:
    """Whether `xs` is a cyclic n-bit Gray code beginning at `start`."""
    return (
        _is_perm(xs, 0, (1 << n) - 1)
        and xs[0] == start
        and all(_one_bit_apart(xs[i - 1], xs[i]) for i in range(len(xs)))
    )


@checker("beautiful-arrangement-ii")
def beautiful_arrangement_ii(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 1..n whose adjacent absolute differences take exactly k distinct values."""
    n, k = args
    return _is_perm(actual, 1, n) and len({abs(a - b) for a, b in pairwise(actual)}) == k


@checker("beautiful-array")
def beautiful_array(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 1..n with no i < k < j where 2 * nums[k] == nums[i] + nums[j]."""
    (n,) = args
    if not _is_perm(actual, 1, n):
        return False
    pos = [0] * (n + 1)
    for i, v in enumerate(actual):
        pos[v] = i
    for k, mid in enumerate(actual):
        twice = 2 * mid
        for v in actual[:k]:
            w = twice - v
            if 1 <= w <= n and pos[w] > k:
                return False
    return True


@checker("circular-permutation-in-binary-representation")
def circular_permutation(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 0..2^n-1 starting at `start` where cyclically adjacent values differ in one bit."""
    n, start = args
    return _is_gray_cycle(actual, n, start)


@checker("convert-integer-to-the-sum-of-two-no-zero-integers")
def no_zero_integers(args: list[Any], expected: Any, actual: Any) -> bool:
    """Two positive integers without a 0 digit that sum to n."""
    (n,) = args
    return _ints(actual) and len(actual) == 2 and sum(actual) == n and all(x > 0 and "0" not in str(x) for x in actual)


@checker("di-string-match")
def di_string_match(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 0..len(s) that rises at each 'I' and falls at each 'D'."""
    (s,) = args
    return _is_perm(actual, 0, len(s)) and all(
        (a < b) == (c == "I") for (a, b), c in zip(pairwise(actual), s, strict=True)
    )


@checker("find-array-given-subset-sums")
def find_array_given_subset_sums(args: list[Any], expected: Any, actual: Any) -> bool:
    """n integers whose 2^n subset sums equal `sums` as a multiset."""
    n, sums = args
    if not _ints(actual) or len(actual) != n:
        return False
    subset_sums = [0]
    for x in actual:
        subset_sums += [s + x for s in subset_sums]
    return sorted(subset_sums) == sorted(sums)


@checker("find-missing-observations")
def find_missing_observations(args: list[Any], expected: Any, actual: Any) -> bool:
    """n rolls in 1..6 bringing the overall mean to `mean`, or [] when no such rolls exist."""
    rolls, mean, n = args
    if expected == []:
        return actual == []
    return (
        _ints(actual)
        and len(actual) == n
        and all(1 <= x <= 6 for x in actual)
        and sum(actual) == mean * (n + len(rolls)) - sum(rolls)
    )


@checker("find-n-unique-integers-sum-up-to-zero")
def sum_zero(args: list[Any], expected: Any, actual: Any) -> bool:
    """n distinct integers that sum to 0."""
    (n,) = args
    return _ints(actual) and len(actual) == n and len(set(actual)) == n and sum(actual) == 0


@checker("gray-code")
def gray_code(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of 0..2^n-1 starting at 0 where cyclically adjacent values differ in one bit."""
    (n,) = args
    return _is_gray_cycle(actual, n, 0)


@checker("largest-divisible-subset")
def largest_divisible_subset(args: list[Any], expected: Any, actual: Any) -> bool:
    """A maximum-size subset of nums in which every pair divides one way."""
    (nums,) = args
    if not _ints(actual) or len(actual) != len(expected) or len(set(actual)) != len(actual):
        return False
    if not set(actual) <= set(nums):
        return False
    chain = sorted(actual)
    return all(b % a == 0 for a, b in pairwise(chain))


@checker("maximum-points-in-an-archery-competition")
def maximum_bob_points(args: list[Any], expected: Any, actual: Any) -> bool:
    """12 non-negative arrow counts summing to numArrows that score Bob the maximum points."""
    num_arrows, alice = args

    def score(bob: list[int]) -> int:
        return sum(k for k, (a, b) in enumerate(zip(alice, bob, strict=True)) if b > a)

    return (
        _ints(actual)
        and len(actual) == len(alice)
        and all(x >= 0 for x in actual)
        and sum(actual) == num_arrows
        and score(actual) == score(expected)
    )


@checker("recover-the-original-array")
def recover_the_original_array(args: list[Any], expected: Any, actual: Any) -> bool:
    """n positive integers arr with some k > 0 such that {a - k} + {a + k} equals nums as a multiset."""
    (nums,) = args
    if not _ints(actual) or 2 * len(actual) != len(nums) or not actual or min(actual) < 1:
        return False
    k = min(actual) - min(nums)
    return k > 0 and Counter(nums) == Counter([a - k for a in actual] + [a + k for a in actual])


@checker("split-array-into-fibonacci-sequence")
def split_into_fibonacci(args: list[Any], expected: Any, actual: Any) -> bool:
    """A split of num into at least 3 int32 values with f[i] + f[i+1] == f[i+2], or [] when none exists."""
    (num,) = args
    if expected == []:
        return actual == []
    return (
        _ints(actual)
        and len(actual) >= 3
        and all(0 <= x < INT32_LIMIT for x in actual)
        and all(a + b == c for a, b, c in zip(actual, actual[1:], actual[2:], strict=False))
        and "".join(map(str, actual)) == num
    )
