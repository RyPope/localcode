import shutil
from pathlib import Path

import pytest

from localcode import db
from localcode.importer.build import build_content_db

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    src = tmp_path / "sources"
    (src / "dataset").mkdir(parents=True)
    shutil.copy(FIX / "dataset_rows.jsonl", src / "dataset" / "LeetCodeDataset-train.jsonl")
    shutil.copytree(FIX / "doocs", src / "doocs")
    shutil.copytree(FIX / "companies", src / "companies")
    build_content_db(src, tmp_path / "content.db", progress=lambda *a: None)
    monkeypatch.setattr(db, "CONTENT_DB", tmp_path / "content.db")
    monkeypatch.setattr(db, "USER_DB", tmp_path / "user.db")
    return tmp_path


class FakeRunner:
    """Answers for the reference (python + ref code) from `ref`, for user code from `user`."""

    def __init__(self):
        self.calls = []
        self.user = None  # dict returned for non-reference calls
        self.ref_values = {}  # json(args) -> value

    def __call__(self, req):
        import json
        self.calls.append(req)
        if req["code"].startswith("from typing import *"):  # the fixture rows' reference header
            return {"compile_error": None, "timed_out": False, "memory_kb": 100, "exit_code": 0, "stderr": "",
                    "results": [{"ok": True, "value": self.ref_values[json.dumps(a)], "stdout": "", "ms": 1} for a in req["cases"]]}
        return self.user


@pytest.fixture
def runner():
    return FakeRunner()
