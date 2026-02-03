# Ralph

Ralph is an autonomous agent loop runner.

Operational / CLI usage (TaskMaster tasks, running the loop, MCP server, configuration) lives in `OPERATIONS.md`.

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
- `/prd` - Generate TaskMaster tasks.json directly from feature descriptions
- `/ralph` - Convert existing markdown PRDs to TaskMaster format

Skills are automatically invoked when you ask your agent to:
- "create tasks", "generate tasks.json", "plan this feature", "use the prd skill"
- "convert this prd", "turn into taskmaster format", "use the ralph skill"

### Configure Amp auto-handoff (recommended)

Add to `~/.config/amp/settings.json`:

```json
{
  "amp.experimental.autoHandoff": { "context": 90 }
}
```

This enables automatic handoff when context fills up, allowing Ralph to handle large stories that exceed a single context window.

## Workflow

### 1. Generate Tasks with PRD Skill

Use the PRD skill to generate TaskMaster tasks directly:

```
Use the prd skill to create tasks for [your feature description]
```

The skill will:
1. Ask 3-5 clarifying questions with lettered options (answer like "1A, 2C, 3B")
2. Generate `.taskmaster/tasks/tasks.json` with properly sized tasks
3. Set up dependency tracking and priority ordering
4. Optionally save a markdown PRD to `tasks/prd-[feature-name].md` for documentation

**TaskMaster Format** (`.taskmaster/tasks/tasks.json`):
```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Add users table with auth fields",
      "description": "As a developer, I need to store user credentials...",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": ["...", "Typecheck passes"],
      "dependsOn": [],
      "blockedBy": [],
      ...
    }
  ],
  "metadata": {
    "project": "MyApp",
    "branchName": "ralph/feature-name",
    "taskMasterVersion": "1.0"
  }
}
```

### 2. Alternative: Convert Existing PRD

If you have an existing markdown PRD, use the Ralph skill:

```
Use the ralph skill to convert tasks/prd-user-auth.md to TaskMaster format
```

This converts markdown PRDs to `.taskmaster/tasks/tasks.json` with proper task sizing and dependencies.

### 3. Run Ralph

**Using CLI Subcommands**:

```bash
# Run with specific tool and iterations
uv run ralph run --tool amp --max-iterations 10
uv run ralph run --tool claude --max-iterations 5
uv run ralph run --tool codex --max-iterations 20
uv run ralph run --tool opencode --max-iterations 10

# Check status with visual progress display
uv run ralph status

# List all tasks
uv run ralph list-tasks

# List only pending tasks
uv run ralph list-tasks --filter pending

# List in-progress tasks
uv run ralph list-tasks --filter in-progress

# Dry run (test without execution)
uv run ralph run --tool amp --dry-run
```

**Using Justfile Shortcuts** (recommended):

```bash
# Run Ralph
just ralph-amp 10           # Run with Amp
just ralph-claude 5         # Run with Claude Code
just ralph-codex 20         # Run with Codex
just ralph-opencode 10      # Run with OpenCode

# Monitor progress
just ralph-status           # Visual progress with task tree
just ralph-tasks            # List all tasks
just ralph-tasks-pending    # List pending tasks only
just ralph-tasks-active     # List in-progress tasks only

# Testing and validation
just ralph-dry-run amp 3    # Test without execution
just ralph-test             # Run test suite
just ralph-check            # Type check and lint
just ralph-all              # Format, check, and test

# MCP Server
just ralph-mcp              # Run as MCP server (stdio)
just ralph-mcp-http 8000    # Run as MCP server (HTTP)
```

**Using TaskMaster CLI**:

```bash
# Task management
taskmaster task list                        # List all tasks
taskmaster task get task-001                # View task details
taskmaster task update task-001 --status done
taskmaster status                           # Overall status
```

Ralph will:
1. Display visual progress with Unicode box-drawing characters (█ ░ ├─ └─)
2. Create a feature branch (from `.taskmaster/tasks/tasks.json` `metadata.branchName`)
3. Pick the highest priority task where `status: "pending"` and not blocked by `blockedBy` dependencies
4. Set task status to `"in-progress"`
5. Implement that single task following acceptance criteria
6. Run quality checks (typecheck, lint, tests)
7. Commit if checks pass with message: `feat: [Task ID] - [Task Title]`
8. Update task status to `"done"`
9. Append learnings and context to `progress.txt`
10. Repeat until all tasks done, blocked, or max iterations reached
11. Emit `<promise>COMPLETE</promise>` when finished

### 4. Monitor and Manage

While Ralph runs, monitor progress:

```bash
# Real-time status
just ralph-status

# View progress log
tail -f progress.txt

# Check specific task
taskmaster task get task-003

# List what's left
just ralph-tasks-pending
```

### 5. Complete and Review

When Ralph finishes:

```bash
# Review final state
just ralph-status
just ralph-all          # Run all quality checks

# Push and create PR
git push origin ralph/feature-name
gh pr create --title "Add user authentication" --body "Closes #123"
```

## Complete Example

```bash
# 1. Start your agent and generate tasks
amp
> Use the prd skill to create tasks for a user dashboard with stats and charts
> [Answer clarifying questions: 1A, 2C, 3B]

# 2. Verify tasks were created
taskmaster task list
taskmaster status

# 3. Create feature branch
git checkout -b ralph/user-dashboard

# 4. Run Ralph
just ralph-claude 10

# 5. Monitor in another terminal
just ralph-status

# 6. When complete, review and push
just ralph-all
git push origin ralph/user-dashboard
gh pr create
```

## Key Files

| File | Purpose |
|------|---------|
| `ralph/` | Python implementation of Ralph with TaskMaster integration |
| `ralph/README.md` | Detailed technical documentation |
| `OPERATIONS.md` | Operational guide (CLI usage, configuration, MCP server) |
| `CLAUDE.md` | Agent instructions for Claude Code, Codex, and OpenCode |
| `.taskmaster/tasks/tasks.json` | TaskMaster format tasks with status, priorities, dependencies |
| `progress.txt` | Append-only learnings and context for future iterations |
| `justfile` | Task runner commands (ralph-claude, ralph-status, ralph-tasks, etc.) |
| `skills/prd/` | Skill for generating TaskMaster tasks.json directly |
| `skills/ralph/` | Skill for converting markdown PRDs to TaskMaster format |
| `ralph.sh` | Bash wrapper with preflight checks (delegates to Python) |
| `flowchart/` | Interactive visualization of how Ralph works |
| `schemas/taskmaster-schema.json` | JSON schema for TaskMaster format validation |

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
- `.taskmaster/tasks/tasks.json` (which tasks are done, in-progress, or pending)
- `CLAUDE.md` / `AGENTS.md` files (discovered patterns and conventions)

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
