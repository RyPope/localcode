"""Problem catalogue routes."""

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from localcode.services import problems
from localcode.services.models import ProblemDetail, ProblemList, Solution, Tag, Window

router = APIRouter(prefix="/api", tags=["problems"])


@router.get("/problems")
def list_problems(
    q: str = "",
    difficulty: Literal["", "Easy", "Medium", "Hard"] = "",
    status: Literal["", "solved", "attempted", "todo", "unsolved"] = "",
    tags: Annotated[str, Query(description="Comma-separated topics; matches any")] = "",
    company: str = "",
    window: Window = "6m",
    sort: Literal["", "id", "frequency", "acceptance", "difficulty"] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ProblemList:
    return problems.list_problems(q, difficulty, status, tags, company, window, sort, page, page_size)


@router.get("/tags")
def tags() -> list[Tag]:
    return problems.all_tags()


@router.get("/problems/{slug}")
def problem(slug: str) -> ProblemDetail:
    return problems.problem_detail(slug)


@router.get("/problems/{slug}/solutions")
def solutions(slug: str) -> list[Solution]:
    return problems.solutions(slug)
