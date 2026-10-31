from localcode.importer import __main__ as cli
from localcode.importer import pipeline


def test_cli_runs_the_pipeline_and_reports_success(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(pipeline, "fetch_all", lambda dest, log: calls.append("fetch") or {"dataset": "u"})
    monkeypatch.setattr(
        pipeline,
        "build_content_db",
        lambda src, out, progress, used, content_dir=None: (
            calls.append("build") or {"problems": 3, "with_tests": 2, "companies": 1}
        ),
    )
    assert cli.main([]) == 0
    assert calls == ["fetch", "build"]
    assert "imported 3 problems" in capsys.readouterr().out


def test_cli_exits_nonzero_on_failure(monkeypatch, capsys):
    def offline(dest, log):
        raise RuntimeError("all sources failed")

    monkeypatch.setattr(pipeline, "fetch_all", offline)
    assert cli.main([]) == 1
    assert "all sources failed" in capsys.readouterr().err


def test_pipeline_reads_repo_content_and_logs_skipped(monkeypatch, tmp_path):
    from localcode import config
    from localcode.importer import pipeline

    seen = {}
    monkeypatch.setattr(config, "CONTENT_DIR", tmp_path / "content")
    monkeypatch.setattr(pipeline, "fetch_all", lambda dest, log: {"dataset": "x"})

    def fake_build(src, out, progress, used, content_dir=None):
        seen["content_dir"] = content_dir
        return {
            "problems": 1,
            "with_tests": 1,
            "companies": 0,
            "local_problems": 0,
            "skipped": [{"path": "content/problems/x/problem.md", "reason": "bad"}],
        }

    monkeypatch.setattr(pipeline, "build_content_db", fake_build)
    log: list[str] = []
    pipeline.run_import(log.append, lambda *a: None)
    assert seen["content_dir"] == tmp_path / "content"
    assert any("skipped content/problems/x/problem.md: bad" in m for m in log)
