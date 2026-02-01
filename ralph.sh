#!/bin/bash
# Ralph - Autonomous coding agent wrapper
# Handles setup, initialization, preflight checks before delegating to Python runtime

set -e

# Find script directory (handles symlinks)
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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1" >&2
}

error() {
    echo -e "${RED}✗${NC} $1" >&2
    exit 1
}

# 1. Find git repository root
find_git_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

GIT_ROOT=$(find_git_root) || error "Not in a git repository"
info "Git root: $GIT_ROOT"

# 2. Ensure dependencies are synced (uv only, never pip)
if ! command -v uv &> /dev/null; then
    error "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

info "Syncing dependencies with uv..."
uv sync --quiet || warn "uv sync had warnings (this may be normal)"

# 3. Check/initialize .taskmaster directory
TASKMASTER_DIR="$GIT_ROOT/.taskmaster"

if [[ ! -d "$TASKMASTER_DIR" ]]; then
    warn ".taskmaster directory not found, initializing..."

    # Check if taskmaster CLI is available
    if command -v taskmaster &> /dev/null; then
        info "Using taskmaster CLI to initialize"
        (cd "$GIT_ROOT" && taskmaster init)
    else
        # Fallback: Create basic .taskmaster structure manually
        warn "taskmaster CLI not found, creating basic structure"
        mkdir -p "$TASKMASTER_DIR/tasks"

        # Create config.json
        cat > "$TASKMASTER_DIR/config.json" <<EOF
{
  "version": "1.0",
  "model": "claude-sonnet-4-5",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

        # If tasks.json exists in project root, move it to .taskmaster
        if [[ -f "$GIT_ROOT/tasks.json" ]]; then
            info "Moving tasks.json to .taskmaster/tasks/"
            mv "$GIT_ROOT/tasks.json" "$TASKMASTER_DIR/tasks/tasks.json"
        else
            # Create empty tasks.json
            cat > "$TASKMASTER_DIR/tasks/tasks.json" <<EOF
{
  "tasks": [],
  "metadata": {
    "project": "$(basename "$GIT_ROOT")",
    "branchName": "$(git rev-parse --abbrev-ref HEAD)",
    "taskMasterVersion": "1.0",
    "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "updatedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
}
EOF
        fi

        info "Created .taskmaster directory structure"
    fi
fi

# 4. Verify .taskmaster is in .gitignore
GITIGNORE="$GIT_ROOT/.gitignore"

if [[ ! -f "$GITIGNORE" ]]; then
    warn ".gitignore not found, creating..."
    echo ".taskmaster/" > "$GITIGNORE"
    info "Created .gitignore with .taskmaster/"
else
    if ! grep -q "\.taskmaster" "$GITIGNORE"; then
        warn ".taskmaster not in .gitignore, adding..."
        echo "" >> "$GITIGNORE"
        echo "# TaskMaster-AI task storage (managed by taskmaster-ai, not Ralph)" >> "$GITIGNORE"
        echo ".taskmaster/" >> "$GITIGNORE"
        info "Added .taskmaster/ to .gitignore"
    else
        info ".taskmaster is properly gitignored"
    fi
fi

# 5. Verify .taskmaster is actually ignored by git
if git check-ignore "$TASKMASTER_DIR" > /dev/null 2>&1; then
    info "Preflight passed: .taskmaster is gitignored"
else
    error ".taskmaster is NOT gitignored! Add '.taskmaster/' to .gitignore"
fi

# 6. All preflight checks passed, delegate to Python runtime
info "Initialization complete, starting Ralph runtime..."
echo ""

exec uv run ralph "$@"
