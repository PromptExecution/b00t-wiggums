#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp>=3.0.0b1",
# ]
# ///

import sys

from ralph.__main__ import _run


if __name__ == "__main__":
    raise SystemExit(_run())
