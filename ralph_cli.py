#!/usr/bin/env -S uv run --script
# This file implements the CLI entry point for the Ralph Wiggum agent.
# The shebang above uses `uv run --script` so the script can be executed
# directly without a pre-created virtual environment in environments
# where `uv` is installed. When run as a regular Python module
# (e.g. `python ralph_cli.py`), this shebang is ignored.