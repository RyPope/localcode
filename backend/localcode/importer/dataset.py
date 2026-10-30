"""Turn LeetCodeDataset rows into language-neutral problems and test cases."""
import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from localcode.judging.kwargs import parse_kwargs

_DEF_RE = re.compile(r"def (\w+)\(self,?(.*?)\)\s*(?:->\s*(.*?))?:", re.S)
_INPUT_RE = re.compile(r"^\s*Input:\s*(.+)$", re.M)


@dataclass
class DatasetProblem:
    slug: str
    frontend_id: int
    difficulty: str
    tags: list[str]
    description: str
    starter_python: str
    method: str
    params: list[dict]
    ret: str
    ref_python: str
    compare_mode: str
    cases: list[dict] = field(default_factory=list)
    examples: list[list] = field(default_factory=list)

    @property
    def has_tests(self) -> bool:
        return len(self.cases) >= 3 and self.ret != "None"


def _strip_optional(t: str) -> str:
    t = t.strip()
    m = re.fullmatch(r"Optional\[(.*)\]", t)
    return m.group(1).strip() if m else t


def _split_params(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def params_from_starter(starter: str) -> tuple[str, list[dict], str]:
    m = _DEF_RE.search(starter)
    if not m:
        raise ValueError("no method in starter code")
    params = []
    for p in _split_params(m.group(2)):
        name, _, typ = p.partition(":")
        params.append({"name": name.strip(), "type": _strip_optional(typ)})
    return m.group(1), params, _strip_optional(m.group(3) or "None")


def _literal(node: ast.AST) -> Any:
    """A literal, or tree_node([...]) / list_node([...]) unwrapped to its array."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("tree_node", "list_node"):
        if len(node.args) != 1:
            raise ValueError("unexpected helper call")
        return ast.literal_eval(node.args[0])
    return ast.literal_eval(node)


def _positional(call: ast.Call, names: list[str]) -> list | None:
    if call.args or {kw.arg for kw in call.keywords} != set(names) or len(call.keywords) != len(names):
        return None
    by_name = {kw.arg: _literal(kw.value) for kw in call.keywords}
    return [by_name[n] for n in names]


def _is_candidate(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "candidate"


def parse_cases(test_src: str, params: list[dict], ret: str = "") -> list[dict]:
    """Cases from `assert candidate(...) == x` / `is_same_tree(candidate(...), tree_node(x))`.

    Node-typed results are always arrays, so a null ListNode/TreeNode is `[]`.
    """
    names = [p["name"] for p in params]
    try:
        fn = ast.parse(test_src).body[0]
    except (SyntaxError, IndexError):
        return []
    cases = []
    for st in getattr(fn, "body", []):
        if not isinstance(st, ast.Assert):
            continue
        t = st.test
        try:
            if isinstance(t, ast.Compare) and _is_candidate(t.left) and len(t.ops) == 1:
                if isinstance(t.ops[0], (ast.Eq, ast.Is)):
                    call, expected_node = t.left, t.comparators[0]
                else:
                    continue
            elif (
                isinstance(t, ast.Call)
                and isinstance(t.func, ast.Name)
                and t.func.id in ("is_same_tree", "is_same_list")
                and len(t.args) == 2
                and _is_candidate(t.args[0])
            ):
                call, expected_node = t.args[0], t.args[1]
            else:
                continue
            args = _positional(call, names)
            if args is None:
                continue
            expected = _literal(expected_node)
            if expected is None and ret in ("ListNode", "TreeNode"):
                expected = []
            json.dumps(expected)  # must be JSON-representable
            cases.append({"args": args, "expected": expected})
        except (ValueError, TypeError, SyntaxError):
            continue
    return cases


def parse_examples(description: str, params: list[dict]) -> list[list]:
    names = [p["name"] for p in params]
    examples = []
    for m in _INPUT_RE.finditer(description):
        try:
            kw = parse_kwargs(m.group(1))
        except ValueError:
            continue
        if set(kw) == set(names):
            examples.append([kw[n] for n in names])
    return examples


def load_rows(path: Path | str) -> Iterator[DatasetProblem]:
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            try:
                method, params, ret = params_from_starter(r["starter_code"])
            except ValueError:
                continue
            desc = r["problem_description"]
            yield DatasetProblem(
                slug=r["task_id"],
                frontend_id=int(r["question_id"]),
                difficulty=r["difficulty"],
                tags=r["tags"],
                description=desc,
                starter_python=r["starter_code"].rstrip() + "\n        \n",
                method=method,
                params=params,
                ret=ret,
                ref_python=r["prompt"] + "\n\n" + r["completion"],
                compare_mode="any_order" if "in any order" in desc.lower() else "exact",
                cases=parse_cases(r["test"], params, ret),
                examples=parse_examples(desc, params),
            )
