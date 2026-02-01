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

# Display instructions for creating TaskMaster tasks
show_task_creation_instructions() {
    echo ""
    echo "To create tasks with the prd skill, run your designated agent with this prompt:"
    echo ""
    cat <<'EOF'
Use the prd skill to generate TaskMaster tasks.json for this repo.
Requirements:
- Output must be TaskMaster format with tasks[] and metadata.
- Include 3-7 small, actionable tasks with acceptance criteria.
- Use IETF 2119 MUST/SHOULD/MAY in acceptance criteria.
- Set metadata.project and metadata.branchName appropriately.
EOF
    echo ""
    echo "Then re-run: ./ralph.sh --agent <amp|claude|codex> [max_iterations]"
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

# Prefer a repo-local uv cache to avoid permission issues in restricted sandboxes.
export UV_CACHE_DIR="${UV_CACHE_DIR:-$GIT_ROOT/.uv-cache}"
mkdir -p "$UV_CACHE_DIR"

info "Syncing dependencies with uv..."
uv sync --quiet || error "uv sync failed (check permissions/network)."

# 3. Check/initialize .taskmaster directory
TASKMASTER_DIR="$GIT_ROOT/.taskmaster"
TASKMASTER_MODEL="${RALPH_TASKMASTER_MODEL:-gpt-5-codex}"

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

        # If tasks.json exists in project root, move it to .taskmaster
        if [[ -f "$GIT_ROOT/tasks.json" ]]; then
            info "Moving tasks.json to .taskmaster/tasks/"
            mv "$GIT_ROOT/tasks.json" "$TASKMASTER_DIR/tasks/tasks.json"
        fi

        info "Created .taskmaster directory structure (tasks bootstrap pending)"
    fi
fi

# 4. Ensure TaskMaster config is bootstrapped (idempotent)
uv run python - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

taskmaster_dir = Path("${TASKMASTER_DIR}")
taskmaster_dir.mkdir(parents=True, exist_ok=True)
(taskmaster_dir / "tasks").mkdir(exist_ok=True)

config_path = taskmaster_dir / "config.json"
model = "${TASKMASTER_MODEL}"
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

config = {"version": "1.0", "model": model, "created_at": now}
if config_path.exists():
    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError:
        config = {"version": "1.0", "model": model, "created_at": now}

if config.get("model") != model:
    config["model"] = model
if "created_at" not in config:
    config["created_at"] = now
config_path.write_text(json.dumps(config, indent=2) + "\n")
PY

# 5. Require TaskMaster tasks to exist before running
TASKS_FILE="$TASKMASTER_DIR/tasks/tasks.json"
if [[ ! -f "$TASKS_FILE" ]]; then
    warn "TaskMaster tasks.json not found; nothing to do."
    show_task_creation_instructions
    exit 1
fi

uv run python - <<PY
import json
from pathlib import Path

tasks_path = Path("$TASKS_FILE")
try:
    payload = json.loads(tasks_path.read_text())
except json.JSONDecodeError:
    raise SystemExit(2)

tasks = payload.get("tasks") if isinstance(payload, dict) else None
if not tasks:
    raise SystemExit(3)
PY
TASKS_CHECK_EXIT=$?
if [[ $TASKS_CHECK_EXIT -ne 0 ]]; then
    warn "TaskMaster tasks.json is empty or invalid; nothing to do."
    show_task_creation_instructions
    exit 1
fi

# 6. Verify .taskmaster is in .gitignore
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

# 7. Verify .taskmaster is actually ignored by git
if git check-ignore "$TASKMASTER_DIR" > /dev/null 2>&1; then
    info "Preflight passed: .taskmaster is gitignored"
else
    error ".taskmaster is NOT gitignored! Add '.taskmaster/' to .gitignore"
fi

# 8. All preflight checks passed, delegate to Python runtime
info "Initialization complete, starting Ralph runtime..."
echo ""

exec uv run ralph "$@"
