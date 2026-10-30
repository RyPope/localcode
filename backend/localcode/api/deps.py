"""FastAPI dependencies (overridable in tests)."""
from localcode.judging import runner_client
from localcode.services.judge import Runner


def get_runner() -> Runner:
    return runner_client.execute
