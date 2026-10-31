from typing import Any

import pytest

from localcode.judging.compare import judge

# slug -> (args, statement's example answer, other valid answers, invalid answers)
CASES: dict[str, tuple[list[Any], Any, list[Any], list[Any]]] = {
    "custom-sort-string": (
        ["cba", "abcd"],
        "cbad",
        ["dcba", "cdba", "cbda"],
        ["abcd", "cbaa", "cba", "cbade", ["c", "b", "a", "d"]],
    ),
    "find-unique-binary-string": (
        [["111", "011", "001"]],
        "101",
        ["000", "010", "100", "110"],
        ["111", "10", "1010", "1a1", 101],
    ),
    "generate-a-string-with-characters-that-have-odd-counts": (
        [4],
        "pppz",
        ["ohhh", "love", "abcd"],
        ["ppzz", "ppp", "pppZ", "ppp1", "ppppz"],
    ),
    "longest-happy-string": (
        [1, 1, 7],
        "ccaccbcc",
        ["ccbccacc"],
        ["cccaccbc", "ccaccbc", "ccaccacc", "ccdccbcc", "ccaccbccc"],
    ),
    "minimum-remove-to-make-valid-parentheses": (
        ["lee(t(c)o)de)"],
        "lee(t(c)o)de",
        ["lee(t(co)de)", "lee(t(c)ode)"],
        ["lee(t(c)o)d)", "le(t(c)o)de", "lee(t(c)o)de)", "lee(t(c)o)ed", "let(c)o)de", "lee(tc)o)de"],
    ),
    "reorganize-string": (
        ["aab"],
        "aba",
        [],
        ["aab", "ab", "abb", ""],
    ),
    "replace-all-s-to-avoid-consecutive-repeating-characters": (
        ["ubv?w"],
        "ubvaw",
        ["ubvbw", "ubvzw"],
        ["ubvvw", "ubvww", "ubv?w", "ubvAw", "ubva", "abvaw"],
    ),
    "sort-characters-by-frequency": (
        ["tree"],
        "eert",
        ["eetr"],
        ["tree", "eret", "reet", "eer", "eertt"],
    ),
    "string-without-aaa-or-bbb": (
        [1, 2],
        "abb",
        ["bab", "bba"],
        ["aab", "ab", "abbb", "abc", "bbb"],
    ),
    "longest-duplicate-substring": (
        ["banana"],
        "ana",
        [],
        ["an", "nan", "ban", "anan", ""],
    ),
    "longest-unequal-adjacent-groups-subsequence-i": (
        [["e", "a", "b"], [0, 0, 1]],
        ["e", "b"],
        [["a", "b"]],
        [["e", "a"], ["b", "e"], ["e"], ["e", "x"], ["e", "a", "b"]],
    ),
    "longest-unequal-adjacent-groups-subsequence-ii": (
        [["bab", "dab", "cab"], [1, 2, 2]],
        ["bab", "cab"],
        [["bab", "dab"]],
        [["dab", "cab"], ["cab", "bab"], ["bab"], ["bab", "dab", "cab"], ["bab", "xab"]],
    ),
}

# Problems whose example answer has no alternative in the statement get extra cases with several answers.
EXTRA: list[tuple[str, list[Any], Any, list[Any], list[Any]]] = [
    ("reorganize-string", ["aabbc"], "ababc", ["abcab", "cabab", "babac"], ["aabbc", "ababb", "abab"]),
    ("reorganize-string", ["aaab"], "", [], ["abaa", "aaba", "aaab"]),
    ("longest-duplicate-substring", ["abcabxab"], "ab", [], ["bc", "ca", "a", "abc"]),
    ("longest-duplicate-substring", ["abcabcxbca"], "abc", ["bca"], ["cab", "abca", "ab"]),
    ("longest-duplicate-substring", ["abcd"], "", [], ["a", "ab", "abcd"]),
    ("longest-duplicate-substring", ["aaaa"], "aaa", [], ["aa", "aaaa", "aab"]),
    ("longest-happy-string", [7, 1, 0], "aabaa", [], ["aaba", "abaab", "aabaaa", "aabba"]),
    ("longest-happy-string", [0, 0, 1], "c", [], ["", "a", "cc"]),
    ("minimum-remove-to-make-valid-parentheses", ["))(("], "", [], ["()", ")(", "("]),
    (
        "longest-unequal-adjacent-groups-subsequence-i",
        [["a", "b", "c", "d"], [1, 0, 1, 1]],
        ["a", "b", "c"],
        [["a", "b", "d"]],
        [["a", "c", "d"], ["b", "c", "d"], ["a", "b"]],
    ),
    (
        "longest-unequal-adjacent-groups-subsequence-ii",
        [["a", "b", "c", "d"], [1, 2, 3, 4]],
        ["a", "b", "c", "d"],
        [],
        [["a", "b", "c"], ["a", "c", "b", "d"]],
    ),
    (
        "longest-unequal-adjacent-groups-subsequence-ii",
        [["ab", "ac", "bc", "abc"], [1, 2, 1, 2]],
        ["ab", "ac", "bc"],
        [],
        [["ab", "ac", "abc"], ["ab", "bc", "ac"], ["ab", "ac"]],
    ),
]

ALL = [(slug, *case) for slug, case in CASES.items()] + EXTRA


def test_every_slug_has_a_different_valid_answer() -> None:
    covered = {slug for slug, _, _, others, _ in ALL if others}
    assert covered == set(CASES)


def test_every_slug_rejects_invalid_answers() -> None:
    for slug in CASES:
        assert sum(len(bad) for s, _, _, _, bad in ALL if s == slug) >= 2


@pytest.mark.parametrize(("slug", "args", "example", "others", "invalid"), ALL)
def test_accepts_valid_answers(slug: str, args: list[Any], example: Any, others: list[Any], invalid: list[Any]) -> None:
    for answer in [example, *others]:
        assert judge(example, answer, f"checker:{slug}", args), answer


@pytest.mark.parametrize(("slug", "args", "example", "others", "invalid"), ALL)
def test_rejects_invalid_answers(
    slug: str, args: list[Any], example: Any, others: list[Any], invalid: list[Any]
) -> None:
    for answer in invalid:
        assert not judge(example, answer, f"checker:{slug}", args), answer


def test_long_duplicate_substring_input_is_fast() -> None:
    s = "ab" * 50_000
    assert judge(s[:-2], s[2:], "checker:longest-duplicate-substring", [s])
    assert not judge(s[:-1], "a" * (len(s) - 1), "checker:longest-duplicate-substring", [s])
