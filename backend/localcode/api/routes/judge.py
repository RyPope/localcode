"""Run and Submit."""
from fastapi import APIRouter, Depends

from localcode.api.deps import get_runner
from localcode.api.schemas import RunRequest, SubmitRequest
from localcode.services import judge
from localcode.services.judge import Runner

router = APIRouter(prefix="/api", tags=["judge"])


@router.post("/run")
def run(body: RunRequest, runner: Runner = Depends(get_runner)) -> dict:
    return judge.run(runner, body.slug, body.lang, body.code, body.custom)


@router.post("/submit")
def submit(body: SubmitRequest, runner: Runner = Depends(get_runner)) -> dict:
    return judge.submit(runner, body.slug, body.lang, body.code)
