"""Language-neutral judging of a solution's output against the expected value.

Modes (stored per problem as `compare_mode`):
- `exact`: equal, with a float tolerance.
- `any_order`: the top-level list may be in any order; inner values must match exactly.
- `any_order_deep`: lists may be in any order at every level (groups of sets, combinations).
- `each_any_order`: the top-level slots are fixed but each slot's list may be in any order.
- `checker:<slug>`: a per-problem checker validates the answer against the inputs.
"""

import json
from typing import Any

from localcode.judging.checkers import CHECKERS

FLOAT_TOL = 1e-5
CHECKER_PREFIX = "checker:"


def _sort_key(x: Any) -> str:
    return json.dumps(x, sort_keys=True)


def _deep_sorted(x: Any) -> Any:
    return sorted((_deep_sorted(e) for e in x), key=_sort_key) if isinstance(x, list) else x


def _sorted_slots(x: Any) -> Any:
    return [sorted(e, key=_sort_key) if isinstance(e, list) else e for e in x]


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


def judge(expected: Any, actual: Any, mode: str = "exact", args: list[Any] | None = None) -> bool:
    """Whether `actual` is a correct answer; `args` are the case's inputs (needed by checkers)."""
    if mode.startswith(CHECKER_PREFIX):
        check = CHECKERS.get(mode.removeprefix(CHECKER_PREFIX))
        if check is not None:
            try:
                return bool(check(args or [], expected, actual))
            except Exception:  # a malformed answer (wrong shape or type) is simply wrong
                return False
        mode = "exact"
    both_lists = isinstance(expected, list) and isinstance(actual, list)
    if mode == "any_order" and both_lists:
        return _eq(sorted(expected, key=_sort_key), sorted(actual, key=_sort_key))
    if mode == "any_order_deep" and both_lists:
        return _eq(_deep_sorted(expected), _deep_sorted(actual))
    if mode == "each_any_order" and both_lists:
        return _eq(_sorted_slots(expected), _sorted_slots(actual))
    return _eq(expected, actual)
