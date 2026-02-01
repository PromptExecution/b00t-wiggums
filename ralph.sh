#!/bin/bash
# Ralph - Autonomous coding agent wrapper
# Delegates to Python implementation via uv

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

exec uv run ralph "$@"
