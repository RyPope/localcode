"""Company routes."""
from fastapi import APIRouter

from localcode.services import companies

router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies")
def list_companies(q: str = "") -> list[dict]:
    return companies.list_companies(q)


@router.get("/companies/{slug}")
def company(slug: str, window: str = "6m") -> dict:
    return companies.company_summary(slug, window)
