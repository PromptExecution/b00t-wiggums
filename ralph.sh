#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop
# Usage: ./ralph.sh --agent amp|claude|codex [max_iterations]

set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    TARGET="$(readlink "$SOURCE")"
    if [[ "$TARGET" = /* ]]; then
        SOURCE="$TARGET"
    else
        SOURCE="$DIR/$TARGET"
    fi
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$SCRIPT_DIR"
exec uv run --script ralphython.py "$@"
