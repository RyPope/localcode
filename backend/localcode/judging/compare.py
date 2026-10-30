"""Language-neutral judging of a solution's output against the expected value."""

import json
from typing import Any

FLOAT_TOL = 1e-5


def _sort_key(x: Any) -> str:
    return json.dumps(x, sort_keys=True)


def _eq(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return isinstance(expected, bool) and isinstance(actual, bool) and expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if isinstance(expected, int) and isinstance(actual, int):
            return expected == actual
        return abs(expected - actual) <= FLOAT_TOL * max(1.0, abs(expected))
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(_eq(e, a) for e, a in zip(expected, actual, strict=False))
    return expected == actual


def judge(expected: Any, actual: Any, mode: str = "exact") -> bool:
    if mode == "any_order" and isinstance(expected, list) and isinstance(actual, list):
        return _eq(sorted(expected, key=_sort_key), sorted(actual, key=_sort_key))
    return _eq(expected, actual)
