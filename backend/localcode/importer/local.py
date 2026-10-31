"""Parse repo-kept content (`content/problems/<slug>/`) into problems and overlays.

A folder whose slug is not upstream is a new problem; otherwise it adds to or overrides the upstream
one. Every file is optional here; build.py and the validator decide what a usable problem needs.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DIFFICULTIES = ("Easy", "Medium", "Hard")
COMPARE_MODES = ("exact", "any_order", "any_order_deep", "each_any_order")
LANG_TAGS = {"python": "python", "python3": "python", "java": "java", "cpp": "cpp", "c++": "cpp", "kotlin": "kotlin"}
PROBLEM_KEYS = {"title", "difficulty", "tags", "id", "compare"}
SOLUTION_KEYS = {"title"}

_FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
_FENCE_RE = re.compile(r"^```[ \t]*([\w+]+)[ \t]*\n(.*?)^```[ \t]*$\n?", re.M | re.S)
_markdown = MarkdownIt("commonmark", {"html": False}).enable("table")


class ContentError(ValueError):
    """A local content file that can't be used; the message says why."""


@dataclass
class LocalSolution:
    title: str
    explanation_md: str
    code: dict[str, str]


@dataclass
class LocalProblem:
    slug: str
    title: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None
    frontend_id: int | None = None
    compare_mode: str | None = None
    description_html: str | None = None
    cases: list[dict] | None = None
    solutions: list[LocalSolution] = field(default_factory=list)


def _front_matter(text: str, allowed: set[str]) -> tuple[dict, str]:
    m = _FRONT_RE.match(text)
    if not m:
        if text.startswith("---"):
            raise ContentError("front matter starts with --- but has no closing --- line")
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ContentError(f"front matter is not valid YAML: {e}") from e
    if not isinstance(meta, dict):
        raise ContentError("front matter must be a mapping of keys to values")
    unknown = sorted(set(map(str, meta)) - allowed)
    if unknown:
        raise ContentError(f"unknown front matter keys: {', '.join(unknown)} (allowed: {', '.join(sorted(allowed))})")
    return meta, text[m.end() :]


def _parse_problem_md(p: LocalProblem, path: Path) -> None:
    meta, body = _front_matter(path.read_text(encoding="utf-8"), PROBLEM_KEYS)
    if "title" in meta:
        if not isinstance(meta["title"], str) or not meta["title"].strip():
            raise ContentError("title must be a non-empty string")
        p.title = meta["title"].strip()
    if "difficulty" in meta:
        if meta["difficulty"] not in DIFFICULTIES:
            raise ContentError(f"difficulty must be one of {', '.join(DIFFICULTIES)}, not {meta['difficulty']!r}")
        p.difficulty = meta["difficulty"]
    if "tags" in meta:
        if not isinstance(meta["tags"], list) or not all(isinstance(t, str) and t for t in meta["tags"]):
            raise ContentError("tags must be a list of strings")
        p.tags = meta["tags"]
    if "id" in meta:
        if not isinstance(meta["id"], int) or isinstance(meta["id"], bool) or meta["id"] <= 0:
            raise ContentError("id must be a positive integer")
        p.frontend_id = meta["id"]
    if "compare" in meta:
        if meta["compare"] not in COMPARE_MODES:
            raise ContentError(f"compare must be one of {', '.join(COMPARE_MODES)}")
        p.compare_mode = meta["compare"]
    if body.strip():
        p.description_html = _markdown.render(body).strip()


def _parse_tests(path: Path) -> list[dict]:
    try:
        cases = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentError(f"not valid JSON: {e}") from e
    if not isinstance(cases, list):
        raise ContentError('must be a JSON list of {"args": [...], "expected": ...} objects')
    for i, c in enumerate(cases):
        if not isinstance(c, dict) or set(c) != {"args", "expected"} or not isinstance(c["args"], list):
            raise ContentError(f'case {i + 1} must be an object with exactly "args" (a list) and "expected"')
    return cases


def _parse_solution(path: Path) -> LocalSolution:
    meta, body = _front_matter(path.read_text(encoding="utf-8"), SOLUTION_KEYS)
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ContentError("a solution needs a `title:` in its front matter")
    code: dict[str, str] = {}
    for tag, src in _FENCE_RE.findall(body):
        lang = LANG_TAGS.get(tag.lower())
        if lang is None:
            continue
        if lang in code:
            raise ContentError(f"more than one {lang} code block")
        code[lang] = src.rstrip() + "\n"
    if not code:
        raise ContentError("no code block tagged python, java, cpp or kotlin")
    explanation = _FENCE_RE.sub(lambda m: "" if m.group(1).lower() in LANG_TAGS else m.group(0), body)
    return LocalSolution(title.strip(), re.sub(r"\n{3,}", "\n\n", explanation).strip(), code)


def _parse_dir(path: Path) -> LocalProblem:
    p = LocalProblem(path.name)
    current = path
    try:
        if not SLUG_RE.match(path.name):
            raise ContentError("folder name must be a lowercase kebab-case slug, like two-sum")
        if (current := path / "problem.md").exists():
            _parse_problem_md(p, current)
        if (current := path / "tests.json").exists():
            p.cases = _parse_tests(current)
        for current in sorted((path / "solutions").glob("*.md")):
            p.solutions.append(_parse_solution(current))
    except ContentError as e:
        raise ContentError(f"{current}: {e}") from e
    except (OSError, UnicodeDecodeError) as e:
        raise ContentError(f"{current}: {e}") from e
    return p


def load_local(root: Path) -> tuple[dict[str, LocalProblem], list[dict]]:
    """Problems under `root/problems`, plus `{"path", "reason"}` for each folder that couldn't be used."""
    problems: dict[str, LocalProblem] = {}
    skipped: list[dict] = []
    base = root / "problems"
    if not base.is_dir():
        return problems, skipped
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        try:
            problems[d.name] = _parse_dir(d)
        except ContentError as e:
            path, _, reason = str(e).partition(": ")
            skipped.append({"path": path, "reason": reason})
    return problems, skipped
