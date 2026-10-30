"""Parse doocs/leetcode problem folders (README_EN.md) into statements and reference solutions."""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

LANG_KEYS = {"Python3": "python", "Java": "java", "C++": "cpp", "Kotlin": "kotlin"}

_H1_RE = re.compile(r"^# \[(\d+)\. (.+?)\]\(https://leetcode\.com/problems/([\w-]+)/?\)", re.M)
_DIFF_RE = re.compile(r"^difficulty:\s*(\w+)", re.M)
_TAGS_RE = re.compile(r"^tags:\s*\n((?:\s+- .+\n)+)", re.M)
_SECTION_RE = re.compile(r"<!-- solution:start -->(.*?)<!-- solution:end -->", re.S)
_TAB_RE = re.compile(r"^#### (.+?)\s*\n+```\w*\n(.*?)```", re.M | re.S)


@dataclass
class DoocsProblem:
    slug: str
    frontend_id: int
    title: str
    difficulty: str
    tags: list[str]
    description_html: str
    solutions: list[dict] = field(default_factory=list)

    def first_code(self, lang: str) -> str | None:
        for s in self.solutions:
            if lang in s["code"]:
                return s["code"][lang]
        return None


def iter_problem_dirs(root: Path) -> Iterator[Path]:
    """Problem folders under `<root>/solution/<range>/<NNNN.Title>/` that have an English README."""
    for readme in sorted((root / "solution").glob("*/*/README_EN.md")):
        yield readme.parent


def _between(text: str, start: str, end: str) -> str:
    i, j = text.find(start), text.find(end)
    return text[i + len(start) : j] if i != -1 and j > i else ""


def _parse_solution(block: str) -> dict:
    head, _, tabs = block.partition("<!-- tabs:start -->")
    m = re.search(r"^### (.+)$", head, re.M)
    title = m.group(1).strip() if m else "Solution"
    if title.lower().startswith("solution ") and ":" in title:
        title = title.split(":", 1)[1].strip()
    explanation = head[m.end() :] if m else head
    explanation = explanation.replace("<!-- thinking:start -->", "").replace("<!-- thinking:end -->", "").strip()
    code = {}
    for lang, src in _TAB_RE.findall(tabs.partition("<!-- tabs:end -->")[0]):
        key = LANG_KEYS.get(lang.strip())
        if key and key not in code:
            code[key] = src.rstrip() + "\n"
    return {"title": title, "explanation_md": explanation, "code": code}


def parse_problem_dir(path: Path) -> DoocsProblem | None:
    text = (path / "README_EN.md").read_text(encoding="utf-8")
    h1 = _H1_RE.search(text)
    if not h1:
        return None
    diff = _DIFF_RE.search(text)
    tags_m = _TAGS_RE.search(text)
    tags = [t.strip()[2:].strip() for t in tags_m.group(1).splitlines() if t.strip()] if tags_m else []
    return DoocsProblem(
        slug=h1.group(3),
        frontend_id=int(h1.group(1)),
        title=h1.group(2).strip(),
        difficulty=diff.group(1) if diff else "",
        tags=tags,
        description_html=_between(text, "<!-- description:start -->", "<!-- description:end -->").strip(),
        solutions=[_parse_solution(b) for b in _SECTION_RE.findall(text)],
    )
