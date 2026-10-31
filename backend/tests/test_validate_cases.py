from localcode.tools.validate_cases import cases_to_exclude


def passing_all_but(n: int, *failing: int) -> list[bool]:
    return [i not in failing for i in range(n)]


def test_a_confident_reference_excludes_on_its_own():
    # A correct typed solution can fail an invalid case in one language while another gets lucky
    # (C++ often reads out of bounds without crashing), so one confident failure is enough.
    outcomes = {"java": passing_all_but(10, 2), "cpp": passing_all_but(10, 5)}
    assert cases_to_exclude(outcomes) == {2, 5}


def test_less_confident_references_must_agree():
    # Each passes 80%: on its own that could be a buggy reference, so only shared failures count.
    outcomes = {"java": passing_all_but(10, 1, 2), "cpp": passing_all_but(10, 2, 3)}
    assert cases_to_exclude(outcomes) == {2}


def test_a_single_trusted_reference_still_decides():
    # Suites with many invalid cases leave the only reference below the confident bar.
    assert cases_to_exclude({"java": passing_all_but(10, 1, 2)}) == {1, 2}


def test_confident_and_less_confident_references_combine():
    outcomes = {"java": passing_all_but(10, 3), "cpp": passing_all_but(10, 0, 1, 2, 4, 6)}
    assert cases_to_exclude(outcomes) == {3}


def test_untrusted_references_are_ignored():
    outcomes = {"java": passing_all_but(10, 4), "cpp": passing_all_but(10, *range(6))}
    assert cases_to_exclude(outcomes) == {4}
    assert cases_to_exclude({"java": [False, False, True]}) == set()
    assert cases_to_exclude({}) == set()


def test_order_only_differences_are_flagged():
    from localcode.tools.validate_cases import differs_only_in_order

    assert differs_only_in_order([[-1, 0, 1], [-1, -1, 2]], [[-1, -1, 2], [0, -1, 1]], "exact", [])
    assert not differs_only_in_order([[1, 2]], [[1, 2]], "exact", [])  # not a failure at all
    assert not differs_only_in_order([[1, 2]], [[1, 3]], "exact", [])  # a real difference
    assert not differs_only_in_order([[1, 2], [3]], [[2, 1], [3]], "any_order_deep", [])
