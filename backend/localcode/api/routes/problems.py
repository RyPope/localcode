"""Problem catalogue routes."""

from fastapi import APIRouter, Query

from localcode.services import problems

router = APIRouter(prefix="/api", tags=["problems"])


@router.get("/problems")
def list_problems(
    q: str = "",
    difficulty: str = "",
    status: str = "",
    tags: str = "",
    company: str = "",
    window: str = "6m",
    sort: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict:
    return problems.list_problems(q, difficulty, status, tags, company, window, sort, page, page_size)


@router.get("/tags")
def tags() -> list[dict]:
    return problems.all_tags()


@router.get("/problems/{slug}")
def problem(slug: str) -> dict:
    return problems.problem_detail(slug)


@router.get("/problems/{slug}/solutions")
def solutions(slug: str) -> list[dict]:
    return problems.solutions(slug)
