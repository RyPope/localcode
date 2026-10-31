"""Import or update problem content from the command line.

docker compose exec -u localcode app python -m localcode.importer
"""

import argparse
import sys

from localcode.importer import pipeline


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description="Download the upstream sources and rebuild content.db.").parse_args(argv)
    last_step = None

    def progress(step: str, done: int, total: int) -> None:
        nonlocal last_step
        if step != last_step:
            print(f"== {step}", flush=True)
            last_step = step

    try:
        pipeline.run_import(lambda msg: print(msg, flush=True), progress)
    except Exception as e:  # report and exit non-zero instead of a traceback
        print(f"import failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
