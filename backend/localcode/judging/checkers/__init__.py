"""Per-problem answer checkers for problems that accept more than one correct answer.

A checker decides whether `actual` is a valid answer for the inputs `args`, given the reference
answer `expected` (useful for comparing an optimum, such as a minimum length). Problems with a
checker are imported with `compare_mode = "checker:<slug>"`. Checkers run on untrusted output, so
any exception counts as a rejection (see `localcode.judging.compare.judge`).
"""

from collections.abc import Callable
from typing import Any

Checker = Callable[[list[Any], Any, Any], bool]
CHECKERS: dict[str, Checker] = {}


def checker(*slugs: str) -> Callable[[Checker], Checker]:
    """Register a checker for one or more problem slugs."""

    def register(fn: Checker) -> Checker:
        for slug in slugs:
            if slug in CHECKERS:
                raise ValueError(f"duplicate checker for {slug}")
            CHECKERS[slug] = fn
        return fn

    return register


# Registers every checker (the modules import `checker` from this package).
from localcode.judging.checkers import arrays, encodings, graphs, grids, numbers, strings  # noqa: E402, F401
