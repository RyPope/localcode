"""The import pipeline: download every source, then build content.db. Shared by the app and the CLI."""

from collections.abc import Callable

from localcode import config, db
from localcode.importer.build import Progress, build_content_db
from localcode.importer.fetch import fetch_all


def run_import(log: Callable[[str], None], progress: Progress) -> dict:
    progress("download", 0, 0)
    used = fetch_all(config.SOURCES_DIR, log)
    log(f"building database (repo content from {config.CONTENT_DIR})")
    stats = build_content_db(config.SOURCES_DIR, db.CONTENT_DB, progress, used, content_dir=config.CONTENT_DIR)
    for s in stats.get("skipped", []):
        log(f"skipped {s['path']}: {s['reason']}")
    log(
        f"imported {stats['problems']} problems ({stats.get('local_problems', 0)} local), "
        f"{stats['with_tests']} with tests, {stats['companies']} companies"
    )
    return stats
