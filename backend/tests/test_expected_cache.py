from localcode.services.judge import ExpectedCache


class Problem(dict):
    """Minimal stand-in for a problems row."""


def problem():
    return Problem(slug="p", method="f", params='[{"name": "x", "type": "int"}]', ret="int", ref_python="ref")


class CountingRunner:
    def __init__(self, scale=1):
        self.calls = 0
        self.scale = scale

    def __call__(self, req):
        self.calls += 1
        return {
            "compile_error": None,
            "timed_out": False,
            "memory_kb": 1,
            "exit_code": 0,
            "stderr": "",
            "results": [{"ok": True, "value": a[0] * self.scale, "stdout": "", "ms": 0} for a in req["cases"]],
        }


def test_values_are_reused_within_a_content_version():
    cache, runner = ExpectedCache(), CountingRunner()
    assert cache.resolve(runner, problem(), [[1], [2]], version="v1") == [1, 2]
    assert cache.resolve(runner, problem(), [[2], [1]], version="v1") == [2, 1]
    assert runner.calls == 1


def test_a_new_content_version_recomputes():
    cache = ExpectedCache()
    cache.resolve(CountingRunner(scale=1), problem(), [[3]], version="v1")
    fresh = CountingRunner(scale=10)
    assert cache.resolve(fresh, problem(), [[3]], version="v2") == [30]
    assert fresh.calls == 1


def test_cache_is_bounded():
    cache, runner = ExpectedCache(max_entries=3), CountingRunner()
    cache.resolve(runner, problem(), [[1], [2], [3], [4]], version="v1")
    assert len(cache) == 3
    runner.calls = 0
    cache.resolve(runner, problem(), [[1]], version="v1")  # evicted, recomputed
    assert runner.calls == 1
