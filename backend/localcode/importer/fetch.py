"""Download upstream sources, trying each mirror in order."""
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable

from localcode import config

Log = Callable[[str], None]

DOOCS_SPARSE = [
    "/solution/**/README_EN.md",
]


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=1800)


def fetch_git(urls: list[str], dest: Path, log: Log, sparse: list[str] | None = None) -> str:
    """Clone (or update) the first reachable URL into dest. Returns the URL used."""
    errors = []
    for url in urls:
        try:
            if (dest / ".git").exists():
                log(f"updating {dest.name} from {url}")
                _git("remote", "set-url", "origin", url, cwd=dest)
                _git("fetch", "--depth", "1", "origin", cwd=dest)
                _git("reset", "--hard", "FETCH_HEAD", cwd=dest)
            else:
                log(f"cloning {url}")
                shutil.rmtree(dest, ignore_errors=True)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if sparse:
                    _git("clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(dest))
                    _git("sparse-checkout", "set", "--no-cone", *sparse, cwd=dest)
                    _git("checkout", "-q", cwd=dest)
                else:
                    _git("clone", "-q", "--depth", "1", url, str(dest))
            return url
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            msg = getattr(e, "stderr", "") or str(e)
            log(f"failed {url}: {msg.strip()[:200]}")
            errors.append(url)
            shutil.rmtree(dest, ignore_errors=True)
    raise RuntimeError(f"all sources failed: {errors}")


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
    raise RuntimeError(f"all sources failed: {bases}")


def fetch_all(dest: Path, log: Log, sources: dict[str, list[str]] | None = None) -> dict[str, str]:
    sources = sources or config.SOURCES
    return {
        "dataset": fetch_files(sources["dataset"], config.DATASET_FILES, dest / "dataset", log),
        "doocs": fetch_git(sources["doocs"], dest / "doocs", log, sparse=DOOCS_SPARSE),
        "companies": fetch_git(sources["companies"], dest / "companies", log),
    }
