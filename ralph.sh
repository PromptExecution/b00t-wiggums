#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop
#
# DEPRECATED: This bash wrapper is deprecated. Use the Python version instead:
#   uv run ralph --tool {amp,claude,codex} [max_iterations]
#   OR: just ralph
#
# This script now delegates to the Python version for backwards compatibility.
# See ralph/README.md for complete documentation.

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
cd "$SCRIPT_DIR"

# Show deprecation notice
echo "⚠️  WARNING: ralph.sh is deprecated. Use 'uv run ralph' instead." >&2
echo "   See ralph/README.md for documentation." >&2
echo "" >&2

# Convert --agent to --tool for backwards compatibility
args=()
for arg in "$@"; do
    if [ "$arg" = "--agent" ]; then
        args+=("--tool")
    else
        args+=("$arg")
    fi
done

# Delegate to Python version
exec uv run ralph "${args[@]}"
