"""Answer checkers: arrays."""

from collections import Counter, deque
from itertools import pairwise
from typing import Any

from localcode.judging.checkers import checker


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _int_list(x: Any, n: int | None = None) -> bool:
    return isinstance(x, list) and (n is None or len(x) == n) and all(_is_int(v) for v in x)


def _permutation_of(actual: Any, source: list[int]) -> bool:
    return _int_list(actual, len(source)) and Counter(actual) == Counter(source)


def _advantage(a: list[int], b: list[int]) -> int:
    return sum(x > y for x, y in zip(a, b, strict=True))


@checker("advantage-shuffle")
def advantage_shuffle(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of nums1 whose advantage over nums2 equals the optimal advantage."""
    nums1, nums2 = args
    return _permutation_of(actual, nums1) and _advantage(actual, nums2) == _advantage(expected, nums2)


@checker("array-with-elements-not-equal-to-average-of-neighbors")
def not_average_of_neighbors(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of nums where no inner element is the average of its two neighbors."""
    return _permutation_of(actual, args[0]) and all(
        2 * actual[i] != actual[i - 1] + actual[i + 1] for i in range(1, len(actual) - 1)
    )


@checker("distant-barcodes")
def distant_barcodes(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of barcodes with no two adjacent values equal."""
    return _permutation_of(actual, args[0]) and all(a != b for a, b in pairwise(actual))


@checker("find-anagram-mappings")
def anagram_mappings(args: list[Any], expected: Any, actual: Any) -> bool:
    """mapping[i] is an index of nums2 holding nums1[i]."""
    nums1, nums2 = args
    n = len(nums2)
    return _int_list(actual, len(nums1)) and all(
        0 <= j < n and nums2[j] == v for v, j in zip(nums1, actual, strict=True)
    )


@checker("find-indices-with-index-and-value-difference-i", "find-indices-with-index-and-value-difference-ii")
def indices_with_differences(args: list[Any], expected: Any, actual: Any) -> bool:
    """[i, j] with |i - j| >= indexDifference and |nums[i] - nums[j]| >= valueDifference, else [-1, -1]."""
    nums, index_diff, value_diff = args
    if not _int_list(actual, 2):
        return False
    if expected == [-1, -1]:
        return actual == [-1, -1]
    i, j = actual
    n = len(nums)
    return 0 <= i < n and 0 <= j < n and abs(i - j) >= index_diff and abs(nums[i] - nums[j]) >= value_diff


@checker("find-subsequence-of-length-k-with-the-largest-sum")
def largest_sum_subsequence(args: list[Any], expected: Any, actual: Any) -> bool:
    """A length-k subsequence of nums whose sum equals the largest possible sum."""
    nums, k = args
    if not _int_list(actual, k) or sum(actual) != sum(expected):
        return False
    it = iter(nums)
    return all(any(v == x for x in it) for v in actual)


@checker("sort-array-by-parity")
def sort_by_parity(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of nums with every even value before every odd value."""
    if not _permutation_of(actual, args[0]):
        return False
    evens = sum(v % 2 == 0 for v in actual)
    return all(v % 2 == 0 for v in actual[:evens])


@checker("sort-array-by-parity-ii")
def sort_by_parity_ii(args: list[Any], expected: Any, actual: Any) -> bool:
    """A permutation of nums where each value's parity matches its index's parity."""
    return _permutation_of(actual, args[0]) and all(v % 2 == i % 2 for i, v in enumerate(actual))


@checker("neither-minimum-nor-maximum")
def neither_min_nor_max(args: list[Any], expected: Any, actual: Any) -> bool:
    """A value of nums that is neither its minimum nor its maximum, else -1."""
    nums = args[0]
    if not _is_int(actual):
        return False
    if expected == -1:
        return actual == -1
    return actual in nums and min(nums) < actual < max(nums)


@checker("subarray-with-elements-greater-than-varying-threshold")
def varying_threshold_subarray(args: list[Any], expected: Any, actual: Any) -> bool:
    """A length k such that some length-k subarray has every element > threshold / k, else -1."""
    nums, threshold = args
    if not _is_int(actual):
        return False
    if expected == -1:
        return actual == -1
    k = actual
    if not 1 <= k <= len(nums):
        return False
    window: deque[int] = deque()
    for i, v in enumerate(nums):
        while window and nums[window[-1]] >= v:
            window.pop()
        window.append(i)
        if window[0] <= i - k:
            window.popleft()
        if i >= k - 1 and nums[window[0]] * k > threshold:
            return True
    return False


def _binary_digits(bits: list[int]) -> list[int]:
    for start, b in enumerate(bits):
        if b:
            return bits[start:]
    return []


@checker("three-equal-parts")
def three_equal_parts(args: list[Any], expected: Any, actual: Any) -> bool:
    """[i, j] splitting arr into three non-empty parts with equal binary values, else [-1, -1]."""
    arr = args[0]
    if not _int_list(actual, 2):
        return False
    if expected == [-1, -1]:
        return actual == [-1, -1]
    i, j = actual
    if not (i >= 0 and i + 1 < j < len(arr)):
        return False
    first = _binary_digits(arr[: i + 1])
    return first == _binary_digits(arr[i + 1 : j]) == _binary_digits(arr[j:])


def _split_depth(seq: str, split: Any) -> int:
    if not isinstance(split, list) or len(split) != len(seq):
        raise ValueError("split length must match seq")
    depth = [0, 0]
    best = 0
    for ch, side in zip(seq, split, strict=True):
        if not _is_int(side) or side not in (0, 1):
            raise ValueError("split values must be 0 or 1")
        if ch == "(":
            depth[side] += 1
            best = max(best, depth[side])
        else:
            depth[side] -= 1
            if depth[side] < 0:
                raise ValueError("subsequence is not a valid parentheses string")
    if depth != [0, 0]:
        raise ValueError("subsequence is not a valid parentheses string")
    return best


@checker("maximum-nesting-depth-of-two-valid-parentheses-strings")
def two_vps_split(args: list[Any], expected: Any, actual: Any) -> bool:
    """A 0/1 split of seq into two VPS whose larger nesting depth equals the minimum possible."""
    seq = args[0]
    return _split_depth(seq, actual) == _split_depth(seq, expected)


@checker("fair-candy-swap")
def fair_candy_swap(args: list[Any], expected: Any, actual: Any) -> bool:
    """[a, b] with a in aliceSizes, b in bobSizes, and equal totals after swapping them."""
    alice, bob = args
    if not _int_list(actual, 2):
        return False
    a, b = actual
    return a in set(alice) and b in set(bob) and sum(alice) - a + b == sum(bob) - b + a
