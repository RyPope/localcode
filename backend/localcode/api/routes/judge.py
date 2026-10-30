"""Run and Submit."""

from typing import Annotated

from fastapi import APIRouter, Depends

from localcode.api.deps import get_runner
from localcode.api.schemas import RunRequest, SubmitRequest
from localcode.services import judge
from localcode.services.judge import Runner
from localcode.services.models import RunResult, SubmitResult

router = APIRouter(prefix="/api", tags=["judge"])


@router.post("/run")
def run(body: RunRequest, runner: Annotated[Runner, Depends(get_runner)]) -> RunResult:
    return judge.run(runner, body.slug, body.lang, body.code, body.custom)


@router.post("/submit")
def submit(body: SubmitRequest, runner: Annotated[Runner, Depends(get_runner)]) -> SubmitResult:
    return judge.submit(runner, body.slug, body.lang, body.code)
