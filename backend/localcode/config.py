"""Paths, upstream sources and execution limits."""

import os
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(os.environ.get("LOCALCODE_DATA", "/data"))
CONTENT_DB = DATA_DIR / "content.db"
USER_DB = DATA_DIR / "user.db"
SOURCES_DIR = DATA_DIR / "sources"
RUNNER_URL = os.environ.get("LOCALCODE_RUNNER", "unix:/run/localcode")
WEB_DIST = Path(os.environ.get("LOCALCODE_WEB", Path(__file__).resolve().parent.parent / "web_dist"))


@dataclass(frozen=True)
class Limits:
    """Execution limits; sent with every runner request so the app is their single source of truth."""

    run_per_case_ms: int = 2000
    submit_total_ms: int = 10_000
    memory_mb: int = 1024


LIMITS = Limits()


# Each source is tried in order; extra mirrors can be appended via env (comma-separated).
def _with_mirrors(env: str, defaults: list[str]) -> list[str]:
    extra = [u.strip() for u in os.environ.get(env, "").split(",") if u.strip()]
    return defaults + extra


SOURCES = {
    "dataset": _with_mirrors(
        "LOCALCODE_DATASET_MIRRORS",
        ["https://huggingface.co/datasets/newfacade/LeetCodeDataset/resolve/main"],
    ),
    "doocs": _with_mirrors("LOCALCODE_DOOCS_MIRRORS", ["https://github.com/doocs/leetcode.git"]),
    "companies": _with_mirrors(
        "LOCALCODE_COMPANIES_MIRRORS", ["https://github.com/liquidslr/leetcode-company-wise-problems.git"]
    ),
}
DATASET_FILES = ["LeetCodeDataset-train.jsonl", "LeetCodeDataset-test.jsonl"]
