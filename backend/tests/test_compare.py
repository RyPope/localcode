from localcode.judging.compare import judge


def test_exact_lists():
    assert judge([0, 1], [0, 1])
    assert not judge([0, 1], [1, 0])


def test_float_tolerance():
    assert judge(2.0, 2.000001)
    assert not judge(2.0, 2.01)


def test_int_vs_float():
    assert judge(3, 3.0)


def test_bool_not_int():
    assert not judge(True, 1)
    assert not judge(1, True)


def test_any_order_top_level():
    assert judge([[1, 2], [3]], [[3], [1, 2]], "any_order")


def test_any_order_keeps_inner_order():
    assert not judge([[1, 2]], [[2, 1]], "any_order")


def test_none_vs_empty():
    assert not judge(None, [])


def test_strings():
    assert judge("abc", "abc")
    assert not judge("abc", "abd")


def test_any_order_deep_ignores_order_at_every_level():
    assert judge([[1, 2], [3, 4]], [[4, 3], [2, 1]], "any_order_deep")
    assert judge([["eat", "tea"], ["bat"]], [["bat"], ["tea", "eat"]], "any_order_deep")


def test_any_order_deep_still_checks_contents():
    assert not judge([[1, 2], [3, 4]], [[1, 2], [3, 5]], "any_order_deep")
    assert not judge([[1, 2], [3]], [[1, 2, 3]], "any_order_deep")
    assert not judge([[1, 1], [2]], [[1], [1, 2]], "any_order_deep")


def test_each_any_order_keeps_slots_but_not_their_contents():
    assert judge([[3, 7], [8, 9, 101]], [[7, 3], [101, 8, 9]], "each_any_order")
    assert not judge([[3, 7], [8, 9, 101]], [[8, 9, 101], [3, 7]], "each_any_order")


def test_checker_mode_validates_against_the_inputs():
    from localcode.judging import checkers

    checkers.CHECKERS["test-pair-sum"] = lambda args, expected, actual: sum(args[0][i] for i in actual) == args[1]
    try:
        assert judge([0, 1], [2, 3], "checker:test-pair-sum", args=[[1, 2, 3, 4], 7])
        assert not judge([0, 1], [0, 1], "checker:test-pair-sum", args=[[1, 2, 3, 4], 7])
    finally:
        del checkers.CHECKERS["test-pair-sum"]


def test_checker_that_raises_rejects_the_answer():
    from localcode.judging import checkers

    checkers.CHECKERS["test-raises"] = lambda args, expected, actual: actual[99] > 0
    try:
        assert not judge([1], [1], "checker:test-raises", args=[])
    finally:
        del checkers.CHECKERS["test-raises"]


def test_unknown_checker_falls_back_to_exact():
    assert judge([1, 2], [1, 2], "checker:no-such-problem", args=[])
    assert not judge([1, 2], [2, 1], "checker:no-such-problem", args=[])
