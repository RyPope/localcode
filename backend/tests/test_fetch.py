import subprocess
from pathlib import Path

from localcode.importer.fetch import fetch_files, fetch_git


def make_repo(path: Path) -> str:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    (path / "a.txt").write_text("hello")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"], check=True
    )
    return path.as_uri()


def test_fetch_falls_back_to_mirror(tmp_path):
    good = make_repo(tmp_path / "mirror")
    used = fetch_git([(tmp_path / "missing").as_uri(), good], tmp_path / "out", log=lambda m: None)
    assert used == good
    assert (tmp_path / "out" / "a.txt").read_text() == "hello"


def test_fetch_git_updates_existing_checkout(tmp_path):
    good = make_repo(tmp_path / "mirror")
    fetch_git([good], tmp_path / "out", log=lambda m: None)
    (tmp_path / "mirror" / "a.txt").write_text("v2")
    subprocess.run(
        ["git", "-C", str(tmp_path / "mirror"), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "v2"],
        check=True,
    )
    fetch_git([good], tmp_path / "out", log=lambda m: None)
    assert (tmp_path / "out" / "a.txt").read_text() == "v2"


def test_fetch_files_falls_back(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "f.jsonl").write_text("{}\n")
    used = fetch_files([(tmp_path / "nope").as_uri(), src.as_uri()], ["f.jsonl"], tmp_path / "out", log=lambda m: None)
    assert used == src.as_uri()
    assert (tmp_path / "out" / "f.jsonl").read_text() == "{}\n"


def test_failed_update_keeps_cached_checkout(tmp_path):
    good = make_repo(tmp_path / "mirror")
    fetch_git([good], tmp_path / "out", log=lambda m: None)
    used = fetch_git([(tmp_path / "gone").as_uri()], tmp_path / "out", log=lambda m: None)
    assert used.startswith("cache")
    assert (tmp_path / "out" / "a.txt").read_text() == "hello"


def test_failed_clone_without_cache_still_raises(tmp_path):
    import pytest

    with pytest.raises(RuntimeError):
        fetch_git([(tmp_path / "gone").as_uri()], tmp_path / "out", log=lambda m: None)


def test_fetch_files_uses_cache_when_offline(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "f.jsonl").write_text("old\n")
    used = fetch_files([(tmp_path / "nope").as_uri()], ["f.jsonl"], tmp_path / "out", log=lambda m: None)
    assert used.startswith("cache")
    assert (tmp_path / "out" / "f.jsonl").read_text() == "old\n"
