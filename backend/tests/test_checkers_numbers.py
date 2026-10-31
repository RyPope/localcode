from typing import Any

from localcode.judging.compare import judge


def ok(slug: str, args: list[Any], expected: Any, actual: Any) -> bool:
    return judge(expected, actual, f"checker:{slug}", args)


def test_beautiful_arrangement_ii():
    slug, args, expected = "beautiful-arrangement-ii", [3, 2], [1, 3, 2]
    assert ok(slug, args, expected, [1, 3, 2])
    assert ok(slug, args, expected, [2, 3, 1])
    assert not ok(slug, args, expected, [1, 2, 3])
    assert not ok(slug, args, expected, [1, 3])
    assert not ok(slug, args, expected, [1, 3, 3])
    assert not ok(slug, args, expected, [1, 4, 2])


def test_beautiful_array():
    slug, args, expected = "beautiful-array", [4], [2, 1, 4, 3]
    assert ok(slug, args, expected, [2, 1, 4, 3])
    assert ok(slug, args, expected, [1, 3, 2, 4])
    assert not ok(slug, args, expected, [1, 2, 3, 4])
    assert not ok(slug, args, expected, [2, 1, 4])
    assert not ok(slug, args, expected, [2, 1, 4, 4])
    assert ok(slug, [5], [3, 1, 2, 5, 4], [3, 1, 2, 5, 4])


def test_circular_permutation_in_binary_representation():
    slug, args, expected = "circular-permutation-in-binary-representation", [2, 3], [3, 2, 0, 1]
    assert ok(slug, args, expected, [3, 2, 0, 1])
    assert ok(slug, args, expected, [3, 1, 0, 2])
    assert not ok(slug, args, expected, [2, 3, 1, 0])
    assert not ok(slug, args, expected, [3, 0, 1, 2])
    assert not ok(slug, args, expected, [3, 2, 0])
    assert ok(slug, [3, 2], [2, 6, 7, 5, 4, 0, 1, 3], [2, 6, 7, 5, 4, 0, 1, 3])


def test_convert_integer_to_the_sum_of_two_no_zero_integers():
    slug, args, expected = "convert-integer-to-the-sum-of-two-no-zero-integers", [11], [2, 9]
    assert ok(slug, args, expected, [2, 9])
    assert ok(slug, args, expected, [8, 3])
    assert not ok(slug, args, expected, [1, 10])
    assert not ok(slug, args, expected, [5, 5])
    assert not ok(slug, args, expected, [11, 0])
    assert not ok(slug, args, expected, [2, 9, 0])


def test_di_string_match():
    slug, args, expected = "di-string-match", ["IDID"], [0, 4, 1, 3, 2]
    assert ok(slug, args, expected, [0, 4, 1, 3, 2])
    assert ok(slug, args, expected, [1, 3, 0, 4, 2])
    assert not ok(slug, args, expected, [0, 1, 2, 3, 4])
    assert not ok(slug, args, expected, [0, 4, 1, 3])
    assert not ok(slug, args, expected, [0, 5, 1, 3, 2])


def test_find_array_given_subset_sums():
    slug, args, expected = "find-array-given-subset-sums", [3, [-3, -2, -1, 0, 0, 1, 2, 3]], [1, 2, -3]
    assert ok(slug, args, expected, [1, 2, -3])
    assert ok(slug, args, expected, [-1, -2, 3])
    assert ok(slug, args, expected, [-3, 2, 1])
    assert not ok(slug, args, expected, [1, 2, 3])
    assert not ok(slug, args, expected, [1, 2])
    assert not ok(slug, args, expected, [1, 2, -3, 0])
    assert ok(slug, [2, [0, 0, 0, 0]], [0, 0], [0, 0])


def test_find_missing_observations():
    slug, args, expected = "find-missing-observations", [[1, 5, 6], 3, 4], [2, 3, 2, 2]
    assert ok(slug, args, expected, [2, 3, 2, 2])
    assert ok(slug, args, expected, [5, 2, 1, 1])
    assert not ok(slug, args, expected, [2, 3, 2, 3])
    assert not ok(slug, args, expected, [7, 1, 1, 0])
    assert not ok(slug, args, expected, [4, 4])
    assert ok(slug, [[1, 2, 3, 4], 6, 4], [], [])
    assert not ok(slug, [[1, 2, 3, 4], 6, 4], [], [6, 6, 6, 6])


def test_find_n_unique_integers_sum_up_to_zero():
    slug, args, expected = "find-n-unique-integers-sum-up-to-zero", [5], [-7, -1, 1, 3, 4]
    assert ok(slug, args, expected, [-7, -1, 1, 3, 4])
    assert ok(slug, args, expected, [-3, -1, 2, -2, 4])
    assert not ok(slug, args, expected, [0, 0, 0, 0, 0])
    assert not ok(slug, args, expected, [-1, 0, 1])
    assert not ok(slug, args, expected, [1, 2, 3, 4, 5])


def test_gray_code():
    slug, args, expected = "gray-code", [2], [0, 1, 3, 2]
    assert ok(slug, args, expected, [0, 1, 3, 2])
    assert ok(slug, args, expected, [0, 2, 3, 1])
    assert not ok(slug, args, expected, [1, 0, 2, 3])
    assert not ok(slug, args, expected, [0, 3, 1, 2])
    assert not ok(slug, args, expected, [0, 1, 3])
    assert not ok(slug, args, expected, [0, 1, 3, 2, 0])


def test_largest_divisible_subset():
    slug, args, expected = "largest-divisible-subset", [[1, 2, 3]], [1, 2]
    assert ok(slug, args, expected, [1, 2])
    assert ok(slug, args, expected, [3, 1])
    assert not ok(slug, args, expected, [2, 3])
    assert not ok(slug, args, expected, [1])
    assert not ok(slug, args, expected, [1, 1])
    assert not ok(slug, args, expected, [1, 4])
    assert ok(slug, [[1, 2, 4, 8]], [1, 2, 4, 8], [8, 4, 2, 1])


def test_maximum_points_in_an_archery_competition():
    slug = "maximum-points-in-an-archery-competition"
    args, expected = [9, [1, 1, 0, 1, 0, 0, 2, 1, 0, 1, 2, 0]], [0, 0, 0, 0, 1, 1, 0, 0, 1, 2, 3, 1]
    assert ok(slug, args, expected, expected)
    args, expected = [5, [0, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1]], [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2]
    assert ok(slug, args, expected, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2])
    assert not ok(slug, args, expected, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2])
    assert not ok(slug, args, expected, [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 2])
    assert not ok(slug, args, expected, [1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2])
    assert not ok(slug, args, expected, [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, -2])


def test_recover_the_original_array():
    slug, args, expected = "recover-the-original-array", [[2, 10, 6, 4, 8, 12]], [3, 7, 11]
    assert ok(slug, args, expected, [3, 7, 11])
    assert ok(slug, args, expected, [9, 5, 7])
    assert not ok(slug, args, expected, [3, 7])
    assert not ok(slug, args, expected, [4, 8, 12])
    assert not ok(slug, args, expected, [3, 7, 11, 7])
    assert ok(slug, [[1, 1, 3, 3]], [2, 2], [2, 2])
    assert not ok(slug, [[1, 1, 3, 3]], [2, 2], [1, 3])


def test_split_array_into_fibonacci_sequence():
    slug, args, expected = "split-array-into-fibonacci-sequence", ["1101111"], [11, 0, 11, 11]
    assert ok(slug, args, expected, [11, 0, 11, 11])
    assert ok(slug, args, expected, [110, 1, 111])
    assert not ok(slug, args, expected, [1, 10, 11, 11])
    assert not ok(slug, args, expected, [11, 0, 11])
    assert not ok(slug, args, expected, [])
    assert ok(slug, ["112358130"], [], [])
    assert not ok(slug, ["112358130"], [], [1, 1, 2, 3, 5, 8, 13])
    assert not ok(slug, ["0123"], [], [0, 1, 23])
