from localcode.compare import judge


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
