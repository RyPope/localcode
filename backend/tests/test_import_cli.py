from localcode.importer import __main__ as cli
from localcode.importer import pipeline


def test_cli_runs_the_pipeline_and_reports_success(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(pipeline, "fetch_all", lambda dest, log: calls.append("fetch") or {"dataset": "u"})
    monkeypatch.setattr(
        pipeline,
        "build_content_db",
        lambda src, out, progress, used: calls.append("build") or {"problems": 3, "with_tests": 2, "companies": 1},
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
