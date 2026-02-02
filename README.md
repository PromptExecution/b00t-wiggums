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
