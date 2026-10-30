"""Drafts, submissions, stats and export."""

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse

from localcode.api.schemas import DraftRequest
from localcode.services import progress
from localcode.services.models import Draft, Lang, Stats, Submission

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/drafts/{slug}/{lang}")
def get_draft(slug: str, lang: Lang) -> Draft:
    return {"code": progress.get_draft(slug, lang)}


@router.put("/drafts/{slug}/{lang}", status_code=204)
def put_draft(slug: str, lang: Lang, body: DraftRequest) -> Response:
    progress.save_draft(slug, lang, body.code)
    return Response(status_code=204)


@router.get("/submissions/{slug}")
def submissions(slug: str) -> list[Submission]:
    return progress.list_submissions(slug)


@router.get("/stats")
def stats() -> Stats:
    return progress.stats()


@router.get("/export", response_class=JSONResponse)
def export() -> JSONResponse:
    return JSONResponse(
        progress.export(), headers={"Content-Disposition": 'attachment; filename="localcode-progress.json"'}
    )
