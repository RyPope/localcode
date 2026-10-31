"""How each problem's answers are compared, beyond what the statement's wording reveals.

The importer starts from `exact`, or `any_order` when the statement says "in any order", and then
applies this module: a registered checker wins, then the curated modes below.
"""

from localcode.judging.checkers import CHECKERS
from localcode.judging.compare import CHECKER_PREFIX

# Problems whose answers are collections of sets: order is free at every level.
_ANY_ORDER_DEEP = (
    "4sum",
    "combination-sum",
    "combination-sum-iii",
    "combinations",
    "critical-connections-in-a-network",
    "factor-combinations",
    "find-duplicate-file-in-system",
    "group-anagrams",
    "group-shifted-strings",
    "subsets",
    "subsets-ii",
)
# Problems whose answer has fixed slots, each an unordered list.
_EACH_ANY_ORDER = (
    "find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree",
    "find-the-difference-of-two-arrays",
)

MODES: dict[str, str] = {
    **dict.fromkeys(_ANY_ORDER_DEEP, "any_order_deep"),
    **dict.fromkeys(_EACH_ANY_ORDER, "each_any_order"),
}


def answer_mode(slug: str, default: str) -> str:
    """The compare mode for `slug`, given the one inferred from its statement."""
    if slug in CHECKERS:
        return f"{CHECKER_PREFIX}{slug}"
    return MODES.get(slug, default)
