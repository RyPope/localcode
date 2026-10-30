"""Drafts, submissions, stats and export."""

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from localcode.api.schemas import DraftRequest, Lang
from localcode.services import progress

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/drafts/{slug}/{lang}")
def get_draft(slug: str, lang: Lang) -> dict:
    return {"code": progress.get_draft(slug, lang)}


@router.put("/drafts/{slug}/{lang}", status_code=204)
def put_draft(slug: str, lang: Lang, body: DraftRequest) -> Response:
    progress.save_draft(slug, lang, body.code)
    return Response(status_code=204)


@router.get("/submissions/{slug}")
def submissions(slug: str) -> list[dict]:
    return progress.list_submissions(slug)


@router.get("/stats")
def stats() -> dict:
    return progress.stats()


@router.get("/export")
def export() -> JSONResponse:
    return JSONResponse(
        progress.export(), headers={"Content-Disposition": 'attachment; filename="localcode-progress.json"'}
    )
