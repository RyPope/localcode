"""Request bodies."""

from typing import Annotated

from pydantic import BaseModel, Field

from localcode.services.models import Lang

MAX_CODE = 200_000
MAX_CUSTOM_CASES = 20
MAX_CUSTOM_CASE = 1_000_000  # characters; large enough for 10^5-element inputs
CustomCase = Annotated[str, Field(max_length=MAX_CUSTOM_CASE)]


class RunRequest(BaseModel):
    slug: str
    lang: Lang
    code: str = Field(max_length=MAX_CODE)
    custom: list[CustomCase] = Field(default_factory=list, max_length=MAX_CUSTOM_CASES)


class SubmitRequest(BaseModel):
    slug: str
    lang: Lang
    code: str = Field(max_length=MAX_CODE)


class DraftRequest(BaseModel):
    code: str = Field(max_length=MAX_CODE)
