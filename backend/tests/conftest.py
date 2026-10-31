import shutil
from pathlib import Path

import pytest

from localcode import db
from localcode.importer.build import build_content_db

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _fresh_expected_cache():
    from localcode.services.judge import expected_cache

    expected_cache.clear()


def _build(tmp_path, monkeypatch, content_dir=None):
    src = tmp_path / "sources"
    (src / "dataset").mkdir(parents=True)
    shutil.copy(FIX / "dataset_rows.jsonl", src / "dataset" / "LeetCodeDataset-train.jsonl")
    shutil.copytree(FIX / "doocs", src / "doocs")
    shutil.copytree(FIX / "companies", src / "companies")
    build_content_db(src, tmp_path / "content.db", progress=lambda *a: None, content_dir=content_dir)
    monkeypatch.setattr(db, "CONTENT_DB", tmp_path / "content.db")
    monkeypatch.setattr(db, "USER_DB", tmp_path / "user.db")
    return tmp_path


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    return _build(tmp_path, monkeypatch)


@pytest.fixture
def local_data_dir(tmp_path, monkeypatch):
    """Fixture sources plus tests/fixtures/content (a new problem and a pair-sum overlay)."""
    return _build(tmp_path, monkeypatch, FIX / "content")


class FakeRunner:
    """Answers reference-solution runs from `ref_values` (keyed by JSON args) and user runs with `user`."""

    def __init__(self):
        self.calls: list[dict] = []
        self.user: dict | None = None
        self.ref_values: dict[str, object] = {}

    def __call__(self, req):
        import json

        self.calls.append(req)
        if req["code"].startswith("from typing import *"):  # the fixture rows' reference header
            return {
                "compile_error": None,
                "timed_out": False,
                "memory_kb": 100,
                "exit_code": 0,
                "stderr": "",
                "results": [
                    {"ok": True, "value": self.ref_values[json.dumps(a)], "stdout": "", "ms": 1} for a in req["cases"]
                ],
            }
        return self.user


@pytest.fixture
def runner():
    return FakeRunner()
