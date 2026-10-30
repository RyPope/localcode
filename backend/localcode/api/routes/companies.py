"""Company routes."""

from fastapi import APIRouter

from localcode.services import companies
from localcode.services.models import Company, CompanySummary, Window

router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies")
def list_companies(q: str = "") -> list[Company]:
    return companies.list_companies(q)


@router.get("/companies/{slug}")
def company(slug: str, window: Window = "6m") -> CompanySummary:
    return companies.company_summary(slug, window)
