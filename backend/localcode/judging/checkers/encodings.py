"""Answer checkers: encodings."""

import re
from itertools import pairwise
from typing import Any

from localcode.judging.checkers import checker

_MOVES = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
_DECIMAL = re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]*)(?:\(([0-9]+)\))?)?")
_EXPRESSION = re.compile(r"([0-9]*)\(([0-9]+)\+([0-9]+)\)([0-9]*)")
_CIDR = re.compile(r"([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})/([0-9]{1,2})")


def _is_subsequence(sub: str, s: str) -> bool:
    it = iter(s)
    return all(c in it for c in sub)


def _no_leading_zero(digits: str) -> bool:
    return digits == "0" or not digits.startswith("0")


@checker("alien-dictionary")
def alien_dictionary(args: list[Any], expected: Any, actual: Any) -> bool:
    """Each present letter exactly once, ordered consistently with every adjacent word pair ("" if none exists)."""
    if expected == "":
        return actual == ""
    words = args[0]
    if not isinstance(actual, str) or len(set(actual)) != len(actual) or set(actual) != set("".join(words)):
        return False
    rank = {c: i for i, c in enumerate(actual)}
    for w1, w2 in pairwise(words):
        diff = next(((a, b) for a, b in zip(w1, w2, strict=False) if a != b), None)
        if diff is None:
            if len(w1) > len(w2):
                return False
        elif rank[diff[0]] > rank[diff[1]]:
            return False
    return True


@checker("alphabet-board-path")
def alphabet_board_path(args: list[Any], expected: Any, actual: Any) -> bool:
    """Moves that stay on the board, spell target, and are as few as the optimum."""
    if not isinstance(actual, str) or len(actual) != len(expected):
        return False
    r = c = 0
    spelled = []
    for move in actual:
        if move == "!":
            spelled.append(chr(ord("a") + 5 * r + c))
            continue
        dr, dc = _MOVES[move]
        r, c = r + dr, c + dc
        if not ((0 <= r < 5 and 0 <= c < 5) or (r, c) == (5, 0)):
            return False
    return "".join(spelled) == args[0]


def _decode(enc: str, i: int, limit: int) -> tuple[str, int]:
    """Decode `enc` from index `i` up to a closing bracket or the end; returns (text, next index)."""
    out: list[str] = []
    size = 0
    while i < len(enc) and enc[i] != "]":
        if enc[i].isascii() and enc[i].islower():
            part, i = enc[i], i + 1
        else:
            start = i
            while i < len(enc) and enc[i].isascii() and enc[i].isdigit():
                i += 1
            digits = enc[start:i]
            if not digits or digits[0] == "0" or i >= len(enc) or enc[i] != "[":
                raise ValueError("malformed encoding")
            inner, i = _decode(enc, i + 1, limit)
            if i >= len(enc) or not inner:
                raise ValueError("malformed encoding")
            i += 1
            if len(inner) * int(digits) > limit:
                raise ValueError("decodes past the input")
            part = inner * int(digits)
            if i - start >= len(part):
                raise ValueError("encoding does not shorten its text")
        size += len(part)
        if size > limit:
            raise ValueError("decodes past the input")
        out.append(part)
    return "".join(out), i


@checker("encode-string-with-shortest-length")
def encode_shortest(args: list[Any], expected: Any, actual: Any) -> bool:
    """Decodes to s with every k[...] group shorter than its text, and is as short as the optimum."""
    s = args[0]
    if not isinstance(actual, str) or len(actual) != len(expected):
        return False
    decoded, end = _decode(actual, 0, len(s))
    return end == len(actual) and decoded == s


def _long_division(digits: str, remainder: int, den: int) -> int | None:
    """The remainder after checking `digits` are the next decimal digits of remainder/den, else None."""
    for d in digits:
        remainder *= 10
        if int(d) != remainder // den:
            return None
        remainder %= den
    return remainder


@checker("fraction-to-recurring-decimal")
def fraction_to_decimal(args: list[Any], expected: Any, actual: Any) -> bool:
    """Exactly numerator/denominator: finite without trailing zeros if possible, else a parenthesized repetend."""
    num, den = args
    m = _DECIMAL.fullmatch(actual) if isinstance(actual, str) else None
    if not m:
        return False
    sign, whole, prefix, period = m.groups()
    if (sign == "-") != (num * den < 0) or whole != str(abs(num) // abs(den)):
        return False
    if "." in actual and not prefix and period is None:
        return False
    den = abs(den)
    remainder = _long_division(prefix or "", abs(num) % den, den)
    if period is None:
        return remainder == 0 and not (prefix or "").endswith("0")
    return bool(remainder) and _long_division(period, remainder, den) == remainder


@checker("minimize-result-by-adding-parentheses-to-expression")
def minimize_result(args: list[Any], expected: Any, actual: Any) -> bool:
    """The expression with "(" left of '+' and ")" right of it, evaluating to the optimal value."""

    def value(expr: Any) -> int:
        m = _EXPRESSION.fullmatch(expr)
        if not m or expr.replace("(", "").replace(")", "") != args[0]:
            raise ValueError("not a parenthesization of expression")
        left, a, b, right = m.groups()
        return int(left or 1) * (int(a) + int(b)) * int(right or 1)

    return isinstance(actual, str) and value(actual) == value(expected)


def _abbreviation(abbr: str) -> list[str | int] | None:
    """Tokens of a well-formed abbreviation (letters and positive counts without leading zeros), else None."""
    tokens: list[str | int] = []
    for m in re.finditer(r"[a-z]|[1-9][0-9]*|.", abbr, re.DOTALL):
        tok = m.group(0)
        if tok.isascii() and tok.isdigit():
            tokens.append(int(tok))
        elif tok.isascii() and tok.islower():
            tokens.append(tok)
        else:
            return None
    return tokens


def _abbreviates(tokens: list[str | int], word: str) -> bool:
    i = 0
    for tok in tokens:
        if isinstance(tok, int):
            i += tok
        elif i >= len(word) or word[i] != tok:
            return False
        else:
            i += 1
    return i == len(word)


@checker("minimum-unique-word-abbreviation")
def minimum_unique_abbreviation(args: list[Any], expected: Any, actual: Any) -> bool:
    """An abbreviation of target of optimal length that abbreviates no dictionary word."""
    target, dictionary = args
    if not isinstance(actual, str):
        return False
    tokens, best = _abbreviation(actual), _abbreviation(expected)
    if tokens is None or best is None or len(tokens) != len(best) or not _abbreviates(tokens, target):
        return False
    return not any(len(word) == len(target) and _abbreviates(tokens, word) for word in dictionary)


@checker("shortest-common-supersequence")
def shortest_common_supersequence(args: list[Any], expected: Any, actual: Any) -> bool:
    """Has both strings as subsequences and the optimal length."""
    str1, str2 = args
    return (
        isinstance(actual, str)
        and len(actual) == len(expected)
        and _is_subsequence(str1, actual)
        and _is_subsequence(str2, actual)
    )


@checker("cracking-the-safe")
def cracking_the_safe(args: list[Any], expected: Any, actual: Any) -> bool:
    """Digits below k of length k**n + n - 1 containing every n-digit password."""
    n, k = args
    if not isinstance(actual, str) or len(actual) != k**n + n - 1 or len(actual) != len(expected):
        return False
    if not all(c.isascii() and c.isdigit() and int(c) < k for c in actual):
        return False
    return len({actual[i : i + n] for i in range(len(actual) - n + 1)}) == k**n


@checker("find-the-shortest-superstring")
def shortest_superstring(args: list[Any], expected: Any, actual: Any) -> bool:
    """Contains every word as a substring and has the optimal length."""
    return isinstance(actual, str) and len(actual) == len(expected) and all(w in actual for w in args[0])


@checker("build-an-array-with-stack-operations")
def build_array(args: list[Any], expected: Any, actual: Any) -> bool:
    """Push/Pop over the stream 1..n that first makes the stack equal target on the last operation."""
    target, n = args
    if not isinstance(actual, list) or not actual:
        return False
    stack: list[int] = []
    pushed = 0
    for i, op in enumerate(actual):
        if op == "Push":
            if pushed == n:
                return False
            pushed += 1
            stack.append(pushed)
        elif op == "Pop" and stack:
            stack.pop()
        else:
            return False
        if stack == target:
            return i == len(actual) - 1
    return False


def _cidr_range(block: Any) -> tuple[int, int]:
    """The inclusive address range a canonical CIDR block (no host bits set) covers."""
    m = _CIDR.fullmatch(block)
    if not m or not all(_no_leading_zero(g) for g in m.groups()):
        raise ValueError("malformed CIDR block")
    *octets, prefix = (int(g) for g in m.groups())
    if any(o > 255 for o in octets) or prefix > 32:
        raise ValueError("malformed CIDR block")
    start = int.from_bytes(bytes(octets), "big")
    size = 1 << (32 - prefix)
    if start & (size - 1):
        raise ValueError("the base address has bits set beyond its prefix")
    return start, start + size - 1


@checker("ip-to-cidr")
def ip_to_cidr(args: list[Any], expected: Any, actual: Any) -> bool:
    """As many CIDR blocks as the optimum, together covering exactly [ip, ip + n - 1]."""
    ip, n = args
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    first = int.from_bytes(bytes(int(o) for o in ip.split(".")), "big")
    nxt = first
    for start, end in sorted(_cidr_range(b) for b in actual):
        if start != nxt:
            return False
        nxt = end + 1
    return nxt == first + n
