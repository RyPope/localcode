"""Import status and triggering."""
import json

from fastapi import APIRouter, HTTPException

from localcode import db
from localcode.importer import manager
from localcode.judging import runner_client

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/status")
def status() -> dict:
    meta: dict = {}
    imported = db.CONTENT_DB.exists()
    if imported:
        con = db.connect_content()
        try:
            meta = {k: v for k, v in con.execute("select key, value from meta")}
        finally:
            con.close()
        for key in ("stats", "sources"):
            if key in meta:
                meta[key] = json.loads(meta[key])
    return {"imported": imported, "import": manager.snapshot(), "meta": meta, "toolchains": runner_client.versions()}


@router.post("/import", status_code=202)
def start_import() -> dict:
    if not manager.start():
        raise HTTPException(409, "An import is already running")
    return {"started": True}
