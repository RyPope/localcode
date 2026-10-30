"""Download upstream sources, trying each mirror in order."""

import shutil
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path

from localcode import config

Log = Callable[[str], None]

DOOCS_SPARSE = [
    "/solution/**/README_EN.md",
]


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=1800)


def _clone(url: str, dest: Path, sparse: list[str] | None) -> None:
    shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        if sparse:
            _git("clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(dest))
            _git("sparse-checkout", "set", "--no-cone", *sparse, cwd=dest)
            _git("checkout", "-q", cwd=dest)
        else:
            _git("clone", "-q", "--depth", "1", url, str(dest))
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)  # never leave a half-cloned checkout behind
        raise


def _update(url: str, dest: Path) -> None:
    _git("remote", "set-url", "origin", url, cwd=dest)
    _git("fetch", "--depth", "1", "origin", cwd=dest)
    _git("reset", "--hard", "FETCH_HEAD", cwd=dest)


def fetch_git(urls: list[str], dest: Path, log: Log, sparse: list[str] | None = None) -> str:
    """Clone or update dest from the first reachable URL and return the URL used.

    If every URL fails but an earlier checkout exists, keep it and return "cache (...)".
    """
    cached = (dest / ".git").exists()
    for url in urls:
        try:
            if cached:
                log(f"updating {dest.name} from {url}")
                _update(url, dest)
            else:
                log(f"cloning {url}")
                _clone(url, dest, sparse)
            return url
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            msg = getattr(e, "stderr", "") or str(e)
            log(f"failed {url}: {msg.strip()[:200]}")
    if cached:
        log(f"all sources unreachable; using the cached copy of {dest.name}")
        return "cache (previous download)"
    raise RuntimeError(f"all sources failed for {dest.name}: {urls}")


def fetch_files(bases: list[str], files: list[str], dest: Path, log: Log) -> str:
    """Download every file from the first base URL that serves all of them."""
    dest.mkdir(parents=True, exist_ok=True)
    for base in bases:
        try:
            for name in files:
                log(f"downloading {base.rstrip('/')}/{name}")
                tmp = dest / (name + ".part")
                with urllib.request.urlopen(f"{base.rstrip('/')}/{name}", timeout=60) as r, open(tmp, "wb") as out:
                    shutil.copyfileobj(r, out)
                tmp.replace(dest / name)
            return base
        except OSError as e:
            log(f"failed {base}: {e}")
    if all((dest / name).exists() for name in files):
        log(f"all sources unreachable; using the cached copy of {dest.name}")
        return "cache (previous download)"
    raise RuntimeError(f"all sources failed for {dest.name}: {bases}")


def fetch_all(dest: Path, log: Log, sources: dict[str, list[str]] | None = None) -> dict[str, str]:
    sources = sources or config.SOURCES
    return {
        "dataset": fetch_files(sources["dataset"], config.DATASET_FILES, dest / "dataset", log),
        "doocs": fetch_git(sources["doocs"], dest / "doocs", log, sparse=DOOCS_SPARSE),
        "companies": fetch_git(sources["companies"], dest / "companies", log),
    }
