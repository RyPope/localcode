"""Write the API's OpenAPI document (the source for the web client's generated types).

    python -m localcode.tools.openapi web/openapi.json
"""

import json
import sys
from pathlib import Path

from localcode.api.app import create_app


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    out = Path(args[0]) if args else Path("openapi.json")
    out.write_text(json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
