"""FastAPI app: JSON API under /api plus the built web UI."""
import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from localcode import config, db, runner_client, service
from localcode.importer import manager

@asynccontextmanager
async def lifespan(_: FastAPI):
    if not db.CONTENT_DB.exists():
        manager.start()
    yield


app = FastAPI(title="localcode", lifespan=lifespan)


def get_runner():
    return runner_client.execute


@app.exception_handler(service.ServiceError)
def _service_error(_: Request, e: service.ServiceError):
    return JSONResponse({"detail": e.message}, status_code=e.status)


class RunBody(BaseModel):
    slug: str
    lang: str
    code: str
    custom: list[str] = []


class SubmitBody(BaseModel):
    slug: str
    lang: str
    code: str


class DraftBody(BaseModel):
    code: str


@app.get("/api/status")
def status():
    imported = db.CONTENT_DB.exists()
    meta = {}
    if imported:
        with db.connect_content() as con:
            meta = {r[0]: r[1] for r in con.execute("select key, value from meta")}
        for k in ("stats", "sources"):
            if k in meta:
                meta[k] = json.loads(meta[k])
    return {"imported": imported, "import": manager.state, "meta": meta, "toolchains": runner_client.versions()}


@app.post("/api/import", status_code=202)
def start_import():
    if not manager.start():
        raise HTTPException(409, "An import is already running")
    return {"started": True}


@app.get("/api/problems")
def problems(q: str = "", difficulty: str = "", status: str = "", tags: str = "", company: str = "",
             window: str = "6m", sort: str = "", page: int = 1, page_size: int = 50):
    return service.list_problems(q, difficulty, status, tags, company, window, sort, page, min(page_size, 200))


@app.get("/api/tags")
def tags():
    return service.all_tags()


@app.get("/api/problems/{slug}")
def problem(slug: str):
    return service.problem_detail(slug)


@app.get("/api/problems/{slug}/solutions")
def problem_solutions(slug: str):
    return service.solutions(slug)


@app.get("/api/drafts/{slug}/{lang}")
def get_draft(slug: str, lang: str):
    return {"code": service.get_draft(slug, lang)}


@app.put("/api/drafts/{slug}/{lang}", status_code=204)
def put_draft(slug: str, lang: str, body: DraftBody):
    service.save_draft(slug, lang, body.code)
    return Response(status_code=204)


@app.post("/api/run")
def run(body: RunBody, runner=Depends(get_runner)):
    return service.run(runner, body.slug, body.lang, body.code, body.custom)


@app.post("/api/submit")
def submit(body: SubmitBody, runner=Depends(get_runner)):
    return service.submit(runner, body.slug, body.lang, body.code)


@app.get("/api/submissions/{slug}")
def submissions(slug: str):
    return service.list_submissions(slug)


@app.get("/api/companies")
def companies(q: str = ""):
    return service.list_companies(q)


@app.get("/api/companies/{slug}")
def company(slug: str, window: str = "6m"):
    return service.company_summary(slug, window)


@app.get("/api/stats")
def stats():
    return service.stats()


@app.get("/api/export")
def export():
    return JSONResponse(service.export(), headers={"Content-Disposition": 'attachment; filename="localcode-progress.json"'})


@app.get("/{path:path}", include_in_schema=False)
def web(path: str):
    if path.startswith("api/"):
        raise HTTPException(404)
    dist = config.WEB_DIST.resolve()
    target = (dist / path).resolve()
    if path and target.is_file() and dist in target.parents:
        return FileResponse(target)
    index = dist / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "web UI not built"}, status_code=404)
    return FileResponse(index)

