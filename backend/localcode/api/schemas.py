"""Request bodies."""
from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["python", "java", "cpp", "kotlin"]
MAX_CODE = 200_000


class RunRequest(BaseModel):
    slug: str
    lang: Lang
    code: str = Field(max_length=MAX_CODE)
    custom: list[str] = Field(default_factory=list, max_length=20)


class SubmitRequest(BaseModel):
    slug: str
    lang: Lang
    code: str = Field(max_length=MAX_CODE)


class DraftRequest(BaseModel):
    code: str = Field(max_length=MAX_CODE)
