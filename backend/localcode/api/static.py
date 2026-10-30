"""Serves the built single-page app, falling back to index.html for client-side routes."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from localcode import config

router = APIRouter(include_in_schema=False)


@router.get("/{path:path}")
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
    return FileResponse(index, headers={"Cache-Control": "no-cache"})
