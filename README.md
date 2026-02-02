# Ralph

![Ralph](ralph.webp)

[![Ralph Python CI](https://github.com/promptexecution/b00t-wiggums/actions/workflows/python-ci.yml/badge.svg?branch=ralph/python-rewrite)](https://github.com/promptexecution/b00t-wiggums/actions/workflows/python-ci.yml)

Ralph is an autonomous AI agent loop that runs AI coding tools ([Amp](https://ampcode.com), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://codex.anthropic.com), or [OpenCode](https://opencode.ai)) repeatedly until all task items are complete. Each iteration is a fresh instance with clean context. Memory persists via git history, `progress.txt`, and `tasks.json`.

**Python Rewrite**: Ralph has been rewritten in Python with TaskMaster integration for improved task management, visual progress tracking, and enhanced CLI ergonomics. See [ralph/README.md](ralph/README.md) for detailed documentation.

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/).

[Read my in-depth article on how I use Ralph](https://x.com/ryancarson/status/2008548371712135632)

## Prerequisites

- Python 3.11+ with [uv](https://github.com/astral-sh/uv) package manager installed
- One of the following AI coding tools installed and authenticated:
  - [Amp CLI](https://ampcode.com) (default)
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
  - [Codex](https://codex.anthropic.com)
  - [OpenCode](https://opencode.ai) (optional, fourth executor choice)
- A git repository for your project

## Setup

### Option 1: Copy to your project

Copy the ralph files into your project:

```bash
# From your project root
mkdir -p scripts/ralph
cp /path/to/ralph/ralph.sh scripts/ralph/

# Copy the prompt template for your AI tool of choice:
cp /path/to/ralph/prompt.md scripts/ralph/prompt.md    # For Amp
# OR
cp /path/to/ralph/CLAUDE.md scripts/ralph/CLAUDE.md    # For Claude Code

chmod +x scripts/ralph/ralph.sh
```

### Option 2: Install skills globally (Amp)

Copy the skills to your Amp or Claude config for use across all projects:

For AMP
```bash
cp -r skills/prd ~/.config/amp/skills/
cp -r skills/ralph ~/.config/amp/skills/
```

For Claude Code (manual)
```bash
cp -r skills/prd ~/.claude/skills/
cp -r skills/ralph ~/.claude/skills/
```

### Option 3: Use as Claude Code Marketplace

Add the Ralph marketplace to Claude Code:

```bash
/plugin marketplace add snarktank/ralph
```

Then install the skills:

```bash
/plugin install ralph-skills@ralph-marketplace
```

Available skills after installation:
- `/prd` - Generate Product Requirements Documents
- `/ralph` - Convert PRDs to prd.json format

Skills are automatically invoked when you ask Claude to:
- "create a prd", "write prd for", "plan this feature"
- "convert this prd", "turn into ralph format", "create prd.json"

### Configure Amp auto-handoff (recommended)

Add to `~/.config/amp/settings.json`:

```json
{
  "amp.experimental.autoHandoff": { "context": 90 }
}
```

This enables automatic handoff when context fills up, allowing Ralph to handle large stories that exceed a single context window.

## Workflow

### 1. Create a PRD

Use the PRD skill to generate a detailed requirements document:

```
Load the prd skill and create a PRD for [your feature description]
```

Answer the clarifying questions. The skill saves output to `tasks/prd-[feature-name].md`.

### 2. Convert PRD to TaskMaster format

Use the Ralph skill to convert the markdown PRD to TaskMaster JSON:

```
Load the ralph skill and convert tasks/prd-[feature-name].md to tasks.json
```

This creates `tasks.json` with user stories structured for autonomous execution, including dependency tracking and status management.

### 3. Run Ralph

**Python Version (Recommended)**:

```bash
# Run with amp (default)
uv run ralph run --tool amp --max-iterations 10

# Using Claude Code
uv run ralph run --tool claude --max-iterations 5

# Using Codex
uv run ralph run --tool codex --max-iterations 20

# Using OpenCode
uv run ralph run --tool opencode --max-iterations 10

# Check status
uv run ralph status

# List tasks
uv run ralph list-tasks
uv run ralph list-tasks --filter pending

# Or use justfile commands
just ralph          # Run with amp (default)
just ralph-claude   # Run with claude
just ralph-codex    # Run with codex
just ralph-opencode # Run with opencode
```

**Bash Version (Deprecated)**:

```bash
# Using Amp (default)
./ralph.sh [max_iterations]

# Using Claude Code
./ralph.sh --tool claude [max_iterations]
```

Default is 10 iterations. Use `--tool` to select your AI coding tool (amp, claude, codex, or opencode).

Ralph will:
1. Display visual progress with Unicode box-drawing characters
2. Create a feature branch (from tasks.json `metadata.branchName`)
3. Pick the highest priority story where `status: "pending"` and not blocked
4. Set story status to `"in-progress"`
5. Implement that single story
6. Run quality checks (typecheck, tests)
7. Commit if checks pass with message: `feat: [Story ID] - [Story Title]`
8. Update story status to `"done"`
9. Append learnings to `progress.txt`
10. Repeat until all stories done or max iterations reached

## Key Files

| File | Purpose |
|------|---------|
| `ralph/` | Python implementation of Ralph (recommended) |
| `ralph/README.md` | Detailed Python documentation |
| `ralph.sh` | Bash wrapper (delegates to Python version) |
| `prompt.md` | Prompt template for Amp |
| `CLAUDE.md` | Prompt template for Claude Code, Codex, and OpenCode |
| `tasks.json` | User stories with status tracking (pending/in-progress/done) |
| `prd.json.example` | Legacy PRD format (see migration guide below) |
| `progress.txt` | Append-only learnings for future iterations |
| `justfile` | Just commands for Ralph (ralph, ralph-test, ralph-check, etc.) |
| `skills/prd/` | Skill for generating PRDs (works with Amp and Claude Code) |
| `skills/ralph/` | Skill for converting PRDs to TaskMaster JSON (works with Amp and Claude Code) |
| `.claude-plugin/` | Plugin manifest for Claude Code marketplace discovery |
| `flowchart/` | Interactive visualization of how Ralph works |

## Flowchart

[![Ralph Flowchart](ralph-flowchart.png)](https://snarktank.github.io/ralph/)

**[View Interactive Flowchart](https://snarktank.github.io/ralph/)** - Click through to see each step with animations.

The `flowchart/` directory contains the source code. To run locally:

```bash
cd flowchart
npm install
npm run dev
```

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new AI instance** (Amp, Claude Code, Codex, or OpenCode) with clean context. The only memory between iterations is:
- Git history (commits from previous iterations)
- `progress.txt` (learnings and context)
- `tasks.json` (which stories are done, in-progress, or pending)

### Small Tasks

Each PRD item should be small enough to complete in one context window. If a task is too big, the LLM runs out of context before finishing and produces poor code.

Right-sized stories:
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

Too big (split these):
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the API"

### AGENTS.md Updates Are Critical

After each iteration, Ralph updates the relevant `AGENTS.md` files with learnings. This is key because AI coding tools automatically read these files, so future iterations (and future human developers) benefit from discovered patterns, gotchas, and conventions.

Examples of what to add to AGENTS.md:
- Patterns discovered ("this codebase uses X for Y")
- Gotchas ("do not forget to update Z when changing W")
- Useful context ("the settings panel is in component X")

### Feedback Loops

Ralph only works if there are feedback loops:
- Typecheck catches type errors
- Tests verify behavior
- CI must stay green (broken code compounds across iterations)

### Browser Verification for UI Stories

Frontend stories must include "Verify in browser using dev-browser skill" in acceptance criteria. Ralph will use the dev-browser skill to navigate to the page, interact with the UI, and confirm changes work.

### Visual Progress Display

Ralph now shows rich visual feedback with Unicode box-drawing characters:

```
==================================================
Progress: [████████████░░░░░░░░] 60.0%
Completed: 3/5 | In Progress: 1 | Pending: 1 | Blocked: 0
==================================================

Task Tree:
└─ task-001: ✓ TaskMaster integration [done]
├─ task-002: ⚡ OpenCode executor [in-progress]
└─ task-003: ○ CLI refactor [pending]
    └─ (blocked by: task-002)
```

Status icons:
- ✓ = done
- ⚡ = in-progress
- ○ = pending
- 👀 = review
- ✗ = cancelled

### Stop Condition

When all stories have `status: "done"`, Ralph outputs `<promise>COMPLETE</promise>` and the loop exits.

## Debugging

Check current state:

```bash
# Use Ralph CLI to check status
uv run ralph status

# List all tasks
uv run ralph list-tasks

# Filter by status
uv run ralph list-tasks --filter pending
uv run ralph list-tasks --filter in-progress
uv run ralph list-tasks --filter done

# See which stories are done (manual)
cat tasks.json | jq '.tasks[] | {id, title, status}'

# See learnings from previous iterations
cat progress.txt

# Check git history
git log --oneline -10
```

## Customizing the Prompt

After copying `prompt.md` (for Amp) or `CLAUDE.md` (for Claude Code) to your project, customize it for your project:
- Add project-specific quality check commands
- Include codebase conventions
- Add common gotchas for your stack

## Archiving

Ralph automatically archives previous runs when you start a new feature (different `branchName`). Archives are saved to `archive/YYYY-MM-DD-feature-name/`.

## Migration from Bash to Python

The Python version of Ralph maintains the same behavior as the bash version while adding benefits:

### What's the Same
- Same command-line interface (just `--agent` → `--tool`)
- Same file structure (`prd.json`, `progress.txt`)
- Same workflow (iterations, completion signal, archival)
- Same tool support (amp, claude, codex)

### What's Better
- **Type Safety**: Full mypy strict mode type checking
- **Testing**: 92% code coverage with unit and integration tests
- **Error Handling**: Proper exception handling with returns Result types
- **Maintainability**: Modular architecture with clear separation of concerns
- **Development Tools**: justfile commands, ruff linting, comprehensive documentation

### Migration Steps

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Test the Python version**:
   ```bash
   uv run ralph --help
   ```

3. **Update your workflow**:
   - Replace `./ralph.sh` with `uv run ralph` or `just ralph`
   - Update CI/CD scripts if needed
   - Note: `ralph.sh` still works (delegates to Python version)

4. **Customize configuration** (optional):
   - Set environment variables for codex (see [ralph/README.md](ralph/README.md))
   - Update `CLAUDE.md` or `prompt.md` for your project

### Breaking Changes

- CLI flag: `--agent` → `--tool`
- Python 3.11+ required (was: bash)
- `uv` package manager required (was: none)

See [ralph/README.md](ralph/README.md) for complete Python documentation.

## TaskMaster Format Migration

Ralph has migrated from `prd.json` format to TaskMaster's `tasks.json` format for better task management.

### Key Differences

**Old prd.json format:**
```json
{
  "project": "MyApp",
  "branchName": "feature/my-feature",
  "userStories": [
    {
      "id": "US-001",
      "title": "Add feature X",
      "passes": false,
      "priority": 1
    }
  ]
}
```

**New tasks.json format:**
```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Add feature X",
      "description": "As a user, I need...",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": ["..."],
      "dependsOn": [],
      "blockedBy": [],
      "subtasks": [],
      "notes": []
    }
  ],
  "metadata": {
    "project": "MyApp",
    "branchName": "feature/my-feature"
  }
}
```

### New Features in TaskMaster Format

1. **Status Tracking**: `status` field replaces `passes` with three states:
   - `"pending"` - Not started
   - `"in-progress"` - Currently being worked on
   - `"done"` - Completed

2. **Dependency Management**:
   - `dependsOn: []` - Stories that must complete before this one
   - `blockedBy: []` - Active blockers preventing work on this story

3. **Rich Descriptions**: Story field contains full narrative context:
   ```
   "As a [role], I need [capability], so that [benefit].
   Implementation approach: [technical details]
   Acceptance criteria: [specific conditions]"
   ```

4. **Subtasks**: Break large stories into smaller trackable pieces

5. **Notes Array**: Timestamped progress notes added during execution

### Migration Steps

**Option 1: Use the Ralph Skill (Recommended)**

```bash
# Generate new format from existing PRD
Load the ralph skill and convert prd.json to tasks.json format
```

**Option 2: Manual Conversion**

1. Create `tasks.json` with TaskMaster structure
2. Move `userStories` array to `tasks` array
3. Rename `passes: false` → `status: "pending"`
4. Rename `passes: true` → `status: "done"`
5. Move top-level fields to `metadata` object
6. Add empty `dependsOn`, `blockedBy`, `subtasks` arrays
7. Expand `description` to full story format with context

**Example Migration Script:**

```bash
# Backup old format
cp prd.json prd.json.backup

# Convert manually or use jq (simplified example)
cat prd.json | jq '{
  tasks: [.userStories[] | {
    id,
    title,
    description,
    status: (if .passes then "done" else "pending" end),
    priority,
    acceptanceCriteria,
    dependsOn: [],
    blockedBy: [],
    subtasks: [],
    notes: []
  }],
  metadata: {
    project,
    branchName,
    description,
    taskMasterVersion: "1.0"
  }
}' > tasks.json
```

### Benefits of TaskMaster Format

- **Better dependency tracking**: Know what's blocking work
- **Visual progress**: Unicode box-drawing progress bars
- **Richer context**: Full user story format with implementation details
- **Flexible states**: Track in-progress work explicitly
- **CLI commands**: `ralph status` and `ralph list-tasks` for quick checks

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Amp documentation](https://ampcode.com/manual)
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
