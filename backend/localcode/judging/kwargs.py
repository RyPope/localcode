"""Parse LeetCode-style argument strings: `nums = [2,7], target = 9`."""

import ast
import io
import tokenize
from typing import Any

_JSON_NAMES = {"null": "None", "true": "True", "false": "False"}


def _pythonize(s: str) -> str:
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(s).readline):
        if tok.type == tokenize.NAME and tok.string in _JSON_NAMES:
            tok = tok._replace(string=_JSON_NAMES[tok.string])
        out.append(tok)
    return tokenize.untokenize(out)


_VALUE_ERROR = "must be a number, string, boolean, null or list"


def _json_value(value: Any, name: str) -> Any:
    """Restrict literals to JSON-representable values (tuples become lists)."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list | tuple):
        return [_json_value(v, name) for v in value]
    raise ValueError(f"Value for {name!r} {_VALUE_ERROR}")


def parse_kwargs(s: str) -> dict[str, Any]:
    """Parse `name = value, ...` into a dict of JSON-compatible values.

    Raises ValueError with a user-facing message for syntax errors, positional arguments,
    duplicate names, and values JSON cannot represent (sets, bytes, complex, ...).
    """
    try:
        call = ast.parse("f(" + _pythonize(s.strip()) + ")", mode="eval").body
    except (SyntaxError, tokenize.TokenError) as e:
        raise ValueError(f"Could not parse input: {s!r}") from e
    if not isinstance(call, ast.Call) or call.args:
        raise ValueError("Input must be written as name = value pairs")
    result: dict[str, Any] = {}
    for kw in call.keywords:
        if kw.arg is None:
            raise ValueError("Input must be written as name = value pairs")
        if kw.arg in result:
            raise ValueError(f"{kw.arg!r} is given more than once")
        try:
            value = ast.literal_eval(kw.value)
        except ValueError as e:
            raise ValueError(f"Value for {kw.arg!r} is not a literal") from e
        result[kw.arg] = _json_value(value, kw.arg)
    return result
