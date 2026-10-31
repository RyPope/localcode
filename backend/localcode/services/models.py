"""Response shapes returned by services and served by the API.

These are the HTTP contract: FastAPI validates responses against them and publishes them in the
OpenAPI document, from which the web client's TypeScript types are generated (`make api-types`).
"""

from typing import Any, Literal, TypedDict

Lang = Literal["python", "java", "cpp", "kotlin"]
Difficulty = Literal["Easy", "Medium", "Hard"]
Status = Literal["solved", "attempted", "todo"]
Window = Literal["30d", "3m", "6m", "older", "all"]


class Param(TypedDict):
    name: str
    type: str


class DifficultyCounts(TypedDict):
    """[solved, total] per difficulty."""

    easy: list[int]
    medium: list[int]
    hard: list[int]


class ProblemRow(TypedDict):
    slug: str
    id: int | None  # None for repo-kept problems without a number
    title: str
    difficulty: Difficulty
    acceptance: float | None
    tags: list[str]
    frequency: float | None
    status: Status
    has_tests: bool
    local: bool  # from the repo's content/ folder


class ProblemList(TypedDict):
    total: int
    counts: DifficultyCounts
    items: list[ProblemRow]


class Tag(TypedDict):
    name: str
    count: int


class CompanyRef(TypedDict):
    slug: str
    name: str
    frequency: float


class ProblemDetail(TypedDict):
    slug: str
    id: int | None
    local: bool
    title: str
    difficulty: Difficulty
    tags: list[str]
    acceptance: float | None
    description_html: str
    params: list[Param]
    examples: list[list[Any]]
    has_tests: bool
    test_count: int
    langs: list[Lang]
    starters: dict[str, str]
    companies: list[CompanyRef]
    status: Status
    prev: str | None
    next: str | None


class Solution(TypedDict):
    title: str
    explanation_md: str
    code: dict[str, str]
    notes: dict[str, str]
    local: bool


class Draft(TypedDict):
    code: str | None


class RunCase(TypedDict):
    args: list[Any]
    expected: Any
    actual: Any
    stdout: str
    ok: bool
    error: str | None
    ms: float | None


class RunResult(TypedDict):
    verdict: str
    compile_error: str | None
    cases: list[RunCase]


class FailingCase(TypedDict):
    args: list[Any]
    expected: Any
    actual: Any
    stdout: str
    error: str | None


class SubmitResult(TypedDict):
    verdict: str
    passed: int
    total: int
    runtime_ms: float | None
    memory_kb: int
    failing: FailingCase | None
    compile_error: str | None
    submission_id: int


class Submission(TypedDict):
    id: int
    slug: str
    lang: Lang
    code: str
    verdict: str
    passed: int
    total: int
    runtime_ms: float | None
    memory_kb: int | None
    failing: FailingCase | None
    created_at: str


class Company(TypedDict):
    slug: str
    name: str
    count: int


class ProblemRef(TypedDict):
    slug: str
    id: int | None
    title: str
    difficulty: Difficulty


class CompanySummary(TypedDict):
    slug: str
    name: str
    window: Window
    total: int
    windows: dict[str, int]
    by_difficulty: dict[str, int]
    top_topics: list[Tag]
    solved: int
    attempted: int
    next_unsolved: list[ProblemRef]
    updated: str | None


class WeekCount(TypedDict):
    week: str
    easy: int
    medium: int
    hard: int


class TopicProgress(TypedDict):
    name: str
    solved: int
    total: int


class CompanyProgress(TypedDict):
    slug: str
    name: str
    solved: int
    total: int


class Stats(TypedDict):
    since: str | None
    totals: DifficultyCounts
    solved_by_week: list[WeekCount]
    by_topic: list[TopicProgress]
    by_company: list[CompanyProgress]


class ImportState(TypedDict):
    running: bool
    step: str | None
    done: int
    total: int
    log: list[str]
    error: str | None


class SkippedFile(TypedDict):
    path: str
    reason: str


class ImportStats(TypedDict, total=False):
    problems: int
    with_tests: int
    cases: int
    companies: int
    local_problems: int
    local_solutions: int
    kept_problems: int  # kept although their source no longer has them
    kept_solutions: int
    kept_cases: int
    skipped: list[SkippedFile]  # local content files that could not be used


class ContentMeta(TypedDict, total=False):
    imported_at: str
    stats: ImportStats
    sources: dict[str, str]


# Functional form: "import" is a Python keyword.
AppStatus = TypedDict(
    "AppStatus",
    {"imported": bool, "import": ImportState, "meta": ContentMeta, "toolchains": dict[str, str] | None},
)


class ImportStarted(TypedDict):
    started: bool


class Export(TypedDict):
    exported_at: str
    drafts: list[dict[str, Any]]
    submissions: list[dict[str, Any]]
