import pytest

from localcode.kwargs import parse_kwargs


def test_parse_kwargs():
    assert parse_kwargs('nums = [2,7], target = 9, s = "a,b"') == {"nums": [2, 7], "target": 9, "s": "a,b"}


def test_parse_kwargs_python_literals():
    assert parse_kwargs("root = [1,null,2], f = true") == {"root": [1, None, 2], "f": True}


def test_parse_kwargs_keeps_null_inside_strings():
    assert parse_kwargs('s = "null true"') == {"s": "null true"}


def test_parse_kwargs_bad():
    with pytest.raises(ValueError):
        parse_kwargs("nums = [1,")


def test_parse_kwargs_rejects_expressions():
    with pytest.raises(ValueError):
        parse_kwargs("n = __import__('os')")
