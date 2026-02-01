from __future__ import annotations

import sys

from ralph.entrypoint import mcp, main


def _run() -> int:
    # Preserve historical behavior where `--mcp` bypasses argparse so FastMCP can
    # consume its own flags (e.g. transport/port) without this module needing to
    # mirror them.
    if "--mcp" in sys.argv:
        sys.argv.remove("--mcp")
        mcp.run()
        return 0

    return main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(_run())

