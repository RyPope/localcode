from typing import Any

import pytest

from localcode.judging.compare import judge


def accepts(slug: str, args: list[Any], expected: Any, actual: Any) -> bool:
    return judge(expected, actual, f"checker:{slug}", args)


CASES = [
    (
        "alien-dictionary",
        [["wrt", "wrf", "er", "ett", "rftt"]],
        "wertf",
        ["wertf"],
        ["wetrf", "werf", "wertff", "wrtef", 42],
    ),
    ("alien-dictionary", [["z", "x"]], "zx", ["zx"], ["xz", "z", ""]),
    ("alien-dictionary", [["ab", "adc"]], "abcd", ["abcd", "cabd", "abdc", "bacd"], ["adbc", "abc"]),
    ("alien-dictionary", [["z", "x", "z"]], "", [""], ["zx", "xz"]),
    ("alien-dictionary", [["abc", "ab"]], "", [""], ["abc", "cba"]),
    (
        "alphabet-board-path",
        ["leet"],
        "DDR!UURRR!!DDD!",
        ["DDR!UURRR!!DDD!", "RDD!RRRUU!!DDD!"],
        ["DDR!UURRR!!DDDD!U", "DDR!UURRR!!DD!", "RDD!RRRUU!!DDD"],
    ),
    (
        "alphabet-board-path",
        ["zd"],
        "DDDDD!UUUUURRR!",
        ["DDDDD!UUUUURRR!", "DDDDD!UURRRUUU!"],
        ["DDDDD!RRRUUUUU!", "DDDDD!UUUUURRRR!", "DDDDD!UUUUURRX!"],
    ),
    (
        "encode-string-with-shortest-length",
        ["aaaaaaaaaa"],
        "10[a]",
        ["10[a]", "a9[a]", "9[a]a", "5[aa]"],
        ["9[b]a", "10[a", "10[]a", "2[5[a]]", "010[a]", "aaaaaaaaaa"],
    ),
    ("encode-string-with-shortest-length", ["aaaaa"], "5[a]", ["5[a]"], ["aaaaa", "5[a", "5[b]", "4[a]a"]),
    ("encode-string-with-shortest-length", ["aaaa"], "aaaa", ["aaaa"], ["4[a]", "2[aa]", "aaa"]),
    ("encode-string-with-shortest-length", ["abbbabbbcabbbabbbc"], "2[2[abbb]c]", ["2[2[abbb]c]"], ["2[2[a3b]c]"]),
    ("fraction-to-recurring-decimal", [1, 2], "0.5", ["0.5"], ["0.50", "0.5(0)", "0.4(9)", ".5", "00.5"]),
    ("fraction-to-recurring-decimal", [2, 1], "2", ["2"], ["2.", "2.0", "2.(0)", "1.(9)", "-2"]),
    (
        "fraction-to-recurring-decimal",
        [4, 333],
        "0.(012)",
        ["0.(012)", "0.0(120)", "0.(012012)", "0.012(012)"],
        ["0.(012", "0.01(2)", "0.012", "-0.(012)"],
    ),
    ("fraction-to-recurring-decimal", [7, -3], "-2.(3)", ["-2.(3)", "-2.3(3)"], ["2.(3)", "-2.(4)", "-2.33"]),
    ("fraction-to-recurring-decimal", [0, -5], "0", ["0"], ["-0", "0.0"]),
    (
        "minimize-result-by-adding-parentheses-to-expression",
        ["247+38"],
        "2(47+38)",
        ["2(47+38)"],
        ["(247+38)", "2(4)7+38", "2(47+3)8", "2(47+38", "3(47+38)"],
    ),
    (
        "minimize-result-by-adding-parentheses-to-expression",
        ["12+16"],
        "1(2+1)6",
        ["1(2+1)6", "1(2+16)"],
        ["(12+16)", "12+16", "1(2+1)6 ", "1(2+)16"],
    ),
    ("minimum-unique-word-abbreviation", ["apple", ["blade"]], "a4", ["a4"], ["4e", "5", "a3e", "a04"]),
    (
        "minimum-unique-word-abbreviation",
        ["apple", ["blade", "plain", "amber"]],
        "1p3",
        ["1p3", "2p2", "3l1"],
        ["a4", "4e", "1p2e", "1q3", "p4"],
    ),
    (
        "shortest-common-supersequence",
        ["abac", "cab"],
        "cabac",
        ["cabac"],
        ["cabacx", "abac", "cbaac", "cabab"],
    ),
    ("shortest-common-supersequence", ["ab", "ba"], "aba", ["aba", "bab"], ["abba", "ab", "baa"]),
    (
        "cracking-the-safe",
        [2, 2],
        "01100",
        ["01100", "10011", "11001", "00110"],
        ["01101", "011000", "0110", "01120", "0 110"],
    ),
    ("cracking-the-safe", [1, 2], "10", ["10", "01"], ["11", "102", "1"]),
    (
        "find-the-shortest-superstring",
        [["alex", "loves", "leetcode"]],
        "alexlovesleetcode",
        ["alexlovesleetcode", "leetcodelovesalex", "lovesalexleetcode"],
        ["alexlovesleetcod", "alexlovesleetcodex", "alexleetcodelovez"],
    ),
    (
        "build-an-array-with-stack-operations",
        [[1, 3], 3],
        ["Push", "Push", "Pop", "Push"],
        [["Push", "Push", "Pop", "Push"]],
        [["Push", "Push", "Push"], ["Push", "Push", "Pop", "Push", "Push", "Pop"], ["Push", "Pop", "Push"], "Push"],
    ),
    (
        "build-an-array-with-stack-operations",
        [[3], 3],
        ["Push", "Pop", "Push", "Pop", "Push"],
        [["Push", "Pop", "Push", "Pop", "Push"], ["Push", "Push", "Pop", "Pop", "Push"]],
        [["Push", "Push", "Push"], ["Pop", "Push", "Push", "Pop", "Pop", "Push"], ["Push", "Pop", "Push", "Pop"]],
    ),
    (
        "build-an-array-with-stack-operations",
        [[1, 2], 4],
        ["Push", "Push"],
        [["Push", "Push"]],
        [["Push", "Push", "Push", "Pop"], ["Push", "Push", "Pop", "Push"], ["Push", "push"]],
    ),
    (
        "ip-to-cidr",
        ["255.0.0.7", 10],
        ["255.0.0.7/32", "255.0.0.8/29", "255.0.0.16/32"],
        [
            ["255.0.0.7/32", "255.0.0.8/29", "255.0.0.16/32"],
            ["255.0.0.16/32", "255.0.0.7/32", "255.0.0.8/29"],
            ["255.0.0.7/32", "255.0.0.15/29", "255.0.0.16/32"],
        ],
        [
            ["255.0.0.0/28"],
            ["255.0.0.7/32", "255.0.0.8/29"],
            ["255.0.0.7/32", "255.0.0.8/30", "255.0.0.12/30", "255.0.0.16/32"],
            ["255.0.0.07/32", "255.0.0.8/29", "255.0.0.16/32"],
            ["255.0.0.7/32", "255.0.0.8/29", "255.0.0.16/33"],
        ],
    ),
]


@pytest.mark.parametrize(("slug", "args", "expected", "valid", "invalid"), CASES)
def test_checker(slug: str, args: list[Any], expected: Any, valid: list[Any], invalid: list[Any]) -> None:
    assert valid[0] == expected
    for answer in valid:
        assert accepts(slug, args, expected, answer), answer
    for answer in invalid:
        assert not accepts(slug, args, expected, answer), answer


def test_every_slug_has_a_different_valid_answer() -> None:
    assert {slug for slug, *_ in CASES} == {slug for slug, _, _, valid, _ in CASES if len(valid) > 1}
