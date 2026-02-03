# Ralph

Ralph is an autonomous agent loop runner for Amp, Claude Code, Codex, and OpenCode.
Each iteration runs in a fresh agent context until all tasks are done or max iterations are reached.

Operational details (CLI, MCP mode, and config) live in `OPERATIONS.md`.

Repository: [PromptExecution/b00t-wiggums](https://github.com/PromptExecution/b00t-wiggums)

## Prerequisites

- Python 3.11+
- `uv` installed
- One agent CLI installed/authenticated (`amp`, `claude`, `codex`, or `opencode`)
- Node.js/npm (for TaskMaster CLI)
- A git repository for your project

## Install b00t-wiggums

```bash
git clone https://github.com/PromptExecution/b00t-wiggums.git
cd b00t-wiggums
uv sync
```

## Install TaskMaster-AI (CLI)

Ralph currently relies on the `taskmaster` CLI for task operations.

```bash
npm install -g @taskmaster-ai/cli
taskmaster --help
```

Initialize TaskMaster in your target repo (if not already initialized):

```bash
taskmaster init
```

## TaskMaster-AI via MCP (optional)

If you also want TaskMaster available to MCP clients:

```bash
taskmaster mcp start
```

Example MCP client config (stdio servers):

```json
{
  "mcpServers": {
    "taskmaster": {
      "command": "taskmaster",
      "args": ["mcp", "start"]
    },
    "ralph": {
      "command": "uv",
      "args": ["run", "ralph", "--mcp", "--transport", "stdio"]
    }
  }
}
```

## Install Skills (`/ralph-prd` and `/ralph`)

The PRD skill is now in `skills/ralph-prd/` and is invoked as `/ralph-prd`.

### Amp

```bash
mkdir -p ~/.config/amp/skills
cp -r skills/ralph-prd ~/.config/amp/skills/ralph-prd
cp -r skills/ralph ~/.config/amp/skills/ralph
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -r skills/ralph-prd ~/.claude/skills/ralph-prd
cp -r skills/ralph ~/.claude/skills/ralph
```

### Codex

```bash
mkdir -p ~/.codex/skills
cp -r skills/ralph-prd ~/.codex/skills/ralph-prd
cp -r skills/ralph ~/.codex/skills/ralph
```

## Quick Start

1) Generate tasks:

```text
Use the /ralph-prd skill to create TaskMaster tasks for [feature description]
```

2) Verify tasks exist:

```bash
taskmaster list
```

3) Run Ralph:

```bash
uv run ralph run --tool codex --max-iterations 10
# or wrapper:
./ralph.sh --agent codex 10
```

4) Monitor progress:

```bash
uv run ralph status
uv run ralph list-tasks --filter pending
```

## MCP Mode (Ralph Server)

Run Ralph as an MCP server:

```bash
uv run ralph --mcp --transport stdio
# or HTTP:
uv run ralph --mcp --transport http --host 127.0.0.1 --port 8000
```

## Key Files

- `ralph.sh` - Wrapper with preflight checks (`uv sync`, TaskMaster bootstrap, gitignore checks)
- `ralph/` - Python implementation and CLI
- `OPERATIONS.md` - Operational reference
- `.taskmaster/tasks/tasks.json` - TaskMaster task data
- `skills/ralph-prd/` - Source for the `/ralph-prd` skill
- `skills/ralph/` - Source for the `/ralph` conversion skill
- `flowchart/` - Interactive visualization source

## Flowchart

Flowchart source lives in `flowchart/`:

```bash
cd flowchart
npm install
npm run dev
```

Project home: [PromptExecution/b00t-wiggums](https://github.com/PromptExecution/b00t-wiggums)
