"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from localcode import db
from localcode.api import static
from localcode.api.routes import companies, judge, problems, progress, system
from localcode.importer import manager
from localcode.services.errors import ServiceError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not db.CONTENT_DB.exists():
        manager.start()  # first launch: import content in the background
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="localcode", lifespan=lifespan)

    @app.exception_handler(ServiceError)
    def _service_error(_: Request, e: ServiceError) -> JSONResponse:
        return JSONResponse({"detail": e.message}, status_code=e.status)

    for module in (system, problems, judge, companies, progress):
        app.include_router(module.router)
    app.include_router(static.router)  # last: catch-all for the SPA
    return app


app = create_app()
