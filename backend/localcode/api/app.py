"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from localcode import config, db
from localcode.api import security, static
from localcode.api.routes import companies, judge, problems, progress, system
from localcode.db import ContentNotImported
from localcode.importer import manager
from localcode.services.errors import ServiceError


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db.migrate_user_db()  # fail fast at startup rather than on the first request
    if not db.CONTENT_DB.exists():
        manager.start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="localcode", lifespan=lifespan)
    security.install(app, config.ALLOWED_HOSTS)

    @app.exception_handler(ServiceError)
    def _service_error(_: Request, e: ServiceError) -> JSONResponse:
        return JSONResponse({"detail": e.message}, status_code=e.status)

    @app.exception_handler(ContentNotImported)
    def _not_imported(_: Request, __: ContentNotImported) -> JSONResponse:
        return JSONResponse({"detail": "Problem data has not been imported yet"}, status_code=503)

    for module in (system, problems, judge, companies, progress):
        app.include_router(module.router)
    app.include_router(static.router)  # last: catch-all for the SPA
    return app


app = create_app()
