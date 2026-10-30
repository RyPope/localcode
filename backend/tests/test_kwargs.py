import pytest

from localcode.judging.kwargs import parse_kwargs


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


@pytest.mark.parametrize("text", ["nums = {1, 2}", 'nums = b"x"', "target = 1j", "nums = ...", "m = {'a': 1}"])
def test_parse_kwargs_rejects_non_json_values(text):
    with pytest.raises(ValueError, match="must be a number, string, boolean, null or list"):
        parse_kwargs(text)


def test_parse_kwargs_accepts_tuples_as_lists():
    assert parse_kwargs("p = (1, 2)") == {"p": [1, 2]}


def test_parse_kwargs_rejects_duplicate_names():
    with pytest.raises(ValueError, match="nums"):
        parse_kwargs("nums = [1], nums = [2]")
