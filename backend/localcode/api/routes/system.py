"""Import status and triggering."""

from fastapi import APIRouter

from localcode.services import system
from localcode.services.models import AppStatus, ImportStarted

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/status")
def status() -> AppStatus:
    return system.status()


@router.post("/import", status_code=202)
def start_import() -> ImportStarted:
    return system.start_import()
