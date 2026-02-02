# Ralph - Autonomous Coding Agent Loop Runner

Ralph is a Python CLI tool that runs AI coding agents (amp, claude, codex, opencode) in an iterative loop until they complete their tasks or reach a maximum iteration limit. It integrates with TaskMaster for rich task management, visual progress tracking, and dependency management.

## Installation

Ralph uses `uv` for Python package management. No manual installation required - just use `uv run`:

```bash
# Run directly with uv
uv run ralph --help

# Or install globally (optional)
uv tool install --editable .
ralph --help
```

## Usage

### Basic Usage

Ralph now uses subcommands for better discoverability:

```bash
# Run agent loop (default: amp, 10 iterations)
uv run ralph run

# Run with specific tool and iteration count
uv run ralph run --tool claude --max-iterations 5
uv run ralph run --tool codex --max-iterations 20
uv run ralph run --tool opencode --max-iterations 10

# Check status
uv run ralph status

# List tasks
uv run ralph list-tasks
uv run ralph list-tasks --filter pending
uv run ralph list-tasks --filter in-progress
uv run ralph list-tasks --filter done

# Dry-run mode (show what would execute)
uv run ralph run --tool amp --max-iterations 5 --dry-run

# Verbose output
uv run ralph run --tool claude --verbose
```

### Using justfile Commands

The project includes convenient `just` commands:

```bash
# Run ralph with amp (default)
just ralph

# Run with specific tool
just ralph-amp
just ralph-claude
just ralph-codex
just ralph-opencode

# Check status and list tasks
just ralph-status
just ralph-tasks

# Dry-run mode
just ralph-dry-run

# Custom tool and iterations
just ralph amp 15
```

### Command-Line Options

```
usage: ralph [-h] [--version] {run,status,list-tasks} ...

Ralph - Autonomous AI agent loop runner

positional arguments:
  {run,status,list-tasks}
    run                 Run Ralph agent loop
    status              Show current task status
    list-tasks          List all tasks

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

Examples:
  ralph run --tool amp --max-iterations 10
  ralph status
  ralph list-tasks --filter pending
```

#### Run Subcommand

```
usage: ralph run [-h] [--tool {amp,claude,codex,opencode}] [--max-iterations N]
                 [--task-id TASK_ID] [--dry-run] [--verbose]

options:
  --tool {amp,claude,codex,opencode}
                        Tool to run (default: amp)
  --max-iterations N    Maximum iterations (default: 10)
  --task-id TASK_ID     Run specific task only
  --dry-run             Show what would execute without running
  --verbose             Enable verbose output
```

## How It Works

1. **Initialization**: Ralph reads `tasks.json` and `progress.txt` from the project root
2. **TaskMaster Integration**: Connects to TaskMaster (file-based or MCP) for task management
3. **Visual Progress**: Displays Unicode progress bar and task tree with status icons
4. **Branch Detection**: Checks if git branch has changed since last run
5. **Archival**: If branch changed, archives previous run to `archive/{date}-{branch-name}/`
6. **Task Selection**: Picks highest priority task with `status: "pending"` and no blockers
7. **Status Update**: Sets task to `"in-progress"` before execution
8. **Iteration Loop**: Runs the selected tool (amp/claude/codex/opencode) repeatedly
9. **Completion Detection**: Monitors tool output for `<promise>COMPLETE</promise>` signal
10. **Status Update**: Sets completed task to `"done"`
11. **Progress Tracking**: Updates `progress.txt` after each iteration

## Supported Tools

### amp
Runs `amp --dangerously-allow-all` reading from `prompt.md`

### claude
Runs `claude --model sonnet --dangerously-skip-permissions --print < CLAUDE.md`

### codex
Runs `codex exec` with full configuration (see Environment Variables below)

### opencode
Runs `opencode --model {model} < CLAUDE.md` with configurable model (see Environment Variables below)

## Environment Variables

Ralph supports the following environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEX_PROMPT_FILE` | Prompt file for codex | `CLAUDE.md` |
| `CODEX_MODEL` | Codex model to use | `gpt-5-codex` |
| `CODEX_REASONING_EFFORT` | Reasoning effort level | `high` |
| `CODEX_SANDBOX` | Sandbox mode | `workspace-write` |
| `CODEX_FULL_AUTO` | Enable full automation | `true` |
| `CODEX_EXTRA_ARGS` | Additional codex arguments | (empty) |
| `OPENCODE_MODEL` | OpenCode model to use | `opencode-default` |
| `OPENCODE_EXTRA_ARGS` | Additional opencode arguments | (empty) |
| `TASKMASTER_URL` | TaskMaster server URL (if using MCP) | (empty, uses file-based) |

### Example: Custom Codex Configuration

```bash
export CODEX_MODEL="gpt-4-turbo"
export CODEX_REASONING_EFFORT="medium"
export CODEX_FULL_AUTO="false"
uv run ralph --tool codex 15
```

## TaskMaster Integration

Ralph integrates with [TaskMaster-AI](https://github.com/taskmaster-ai/taskmaster) for rich task management and visual progress tracking.

### Task Format

Ralph uses TaskMaster's `tasks.json` format with the following structure:

```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Short task title",
      "description": "Full user story: As a [role], I need [capability], so that [benefit]...",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": ["Criterion 1", "Criterion 2"],
      "dependsOn": ["task-000"],
      "blockedBy": [],
      "subtasks": [],
      "notes": ["2026-02-01: Progress note"],
      "createdAt": "2026-02-01T10:00:00Z",
      "updatedAt": "2026-02-01T10:00:00Z"
    }
  ],
  "metadata": {
    "project": "MyProject",
    "branchName": "feature/my-feature",
    "description": "Feature description",
    "taskMasterVersion": "1.0"
  }
}
```

### Task Status Lifecycle

Tasks progress through three states:
1. **pending** - Not started, ready to work on
2. **in-progress** - Currently being implemented
3. **done** - Successfully completed

Ralph automatically manages status transitions:
- Sets task to `in-progress` before starting work
- Updates to `done` after successful completion
- Only one task is `in-progress` at a time

### Dependency Management

Use `dependsOn` to express task dependencies:

```json
{
  "id": "task-003",
  "title": "Add UI for feature",
  "dependsOn": ["task-001", "task-002"],
  "status": "pending"
}
```

Ralph will skip tasks with unmet dependencies (dependencies not yet `done`).

Use `blockedBy` to track active blockers:

```json
{
  "id": "task-005",
  "title": "Deploy feature",
  "blockedBy": ["Need production credentials"],
  "status": "pending"
}
```

Ralph skips tasks with non-empty `blockedBy` arrays.

### Visual Progress Display

Ralph shows rich terminal output with Unicode box-drawing characters:

```
==================================================
Progress: [████████████░░░░░░░░] 60.0%
Completed: 3/5 | In Progress: 1 | Pending: 1 | Blocked: 0
==================================================

Task Tree:
└─ task-001: ✓ TaskMaster integration [done]
├─ task-002: ⚡ OpenCode executor [in-progress]
└─ task-003: ○ CLI refactor [pending]
    └─ (depends on: task-002)
```

**Status Icons:**
- ✓ = done
- ⚡ = in-progress
- ○ = pending
- 👀 = review
- ✗ = cancelled

### Hybrid Mode: File-Based vs MCP

Ralph supports two modes for TaskMaster integration:

**File-Based (Default):**
- Reads/writes `tasks.json` directly
- No external dependencies
- Fast and simple

**MCP Mode:**
- Connects to TaskMaster MCP server
- Enable with `TASKMASTER_URL` environment variable
- Supports remote task management

To use MCP mode:

```bash
export TASKMASTER_URL="http://localhost:8080"
uv run ralph run --tool amp
```

### CLI Commands for Task Management

```bash
# Show visual progress summary
uv run ralph status

# List all tasks
uv run ralph list-tasks

# Filter tasks by status
uv run ralph list-tasks --filter pending
uv run ralph list-tasks --filter in-progress
uv run ralph list-tasks --filter done
```

## Migration from Bash Version

### What Changed

The original `ralph.sh` bash script has been rewritten in Python for improved:
- **Maintainability**: Type-safe code with mypy strict mode
- **Testability**: Comprehensive unit and integration tests
- **Error Handling**: Proper exception handling and logging
- **Modularity**: Clean separation of concerns across modules

### Bash Version (Deprecated)

The original `ralph.sh` is still available for backwards compatibility but is deprecated:

```bash
# Old way (deprecated)
./ralph.sh --agent amp 10

# New way (recommended)
uv run ralph run --tool amp --max-iterations 10
```

**Note**: The bash version now delegates to the Python version internally.

### Breaking Changes from Bash Version

- CLI now uses subcommands: `ralph run`, `ralph status`, `ralph list-tasks`
- CLI flag changed: `--agent` → `--tool`
- Positional argument changed: `ralph 10` → `ralph run --max-iterations 10`
- File format changed: `prd.json` → `tasks.json` (see migration guide in main README)
- Tool execution uses Python subprocess instead of direct bash execution
- Configuration is now centralized in `ralph/config.py`

### New Features in Python Version

- **TaskMaster Integration**: Rich task management with dependency tracking
- **Visual Progress**: Unicode box-drawing progress bars and task trees
- **Status Management**: Explicit pending/in-progress/done states
- **CLI Subcommands**: `run`, `status`, `list-tasks` for better discoverability
- **OpenCode Support**: Fourth executor option alongside amp/claude/codex
- **Dry-Run Mode**: Preview what would execute without running
- **Task Filtering**: Filter tasks by status (pending/in-progress/done)
- **Dependency Tracking**: Express task dependencies and blockers

## Project Structure

```
ralph/
├── __init__.py           # Package initialization
├── ralph_cli.py          # CLI entry point with subcommands
├── config.py             # Configuration management
├── executors.py          # Tool execution (amp, claude, codex, opencode)
├── file_manager.py       # PRD and progress file operations
├── archiver.py           # Branch change detection and archival
├── runner.py             # Main iteration loop with TaskMaster integration
├── logging_utils.py      # Logging utilities with emoji prefixes
├── taskmaster_adapter.py # TaskMaster integration (file-based and MCP)
└── progress_display.py   # Visual progress bars and task trees
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ralph

# Run only unit tests
uv run pytest tests/test_*.py -k "not integration"

# Run only integration tests
uv run pytest tests/test_ralph_integration.py
```

Or use justfile commands:

```bash
just ralph-test        # Run all tests
just ralph-check       # Type check and lint
just ralph-format      # Format code
just ralph-all         # Format, check, and test
```

### Type Checking

Ralph uses `mypy` in strict mode:

```bash
uv run mypy ralph/
```

### Linting and Formatting

Ralph uses `ruff` for linting and formatting:

```bash
# Check for issues
uv run ruff check ralph/

# Format code
uv run ruff format ralph/
```

## Troubleshooting

### Common Issues

#### Tool Not Found

**Problem**: `ralph: command not found` or `amp/claude/codex not found`

**Solution**: Ensure the selected tool is installed and in your PATH:
```bash
which amp
which claude
which codex
```

#### Permission Denied

**Problem**: `Permission denied` when running tools

**Solution**: Ralph runs tools with `--dangerously-allow-all` or `--dangerously-skip-permissions` flags. Ensure you understand the security implications.

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'ralph'`

**Solution**: Use `uv run` to ensure the virtual environment is activated:
```bash
uv run ralph --help
```

#### Progress File Issues

**Problem**: `Error initializing progress file`

**Solution**: Ensure you have write permissions in the project directory:
```bash
ls -la progress.txt
chmod 644 progress.txt
```

#### Type Check Failures

**Problem**: `mypy` reports type errors

**Solution**: Ralph requires Python 3.11+ and strict type checking. Ensure all type hints are correct:
```bash
uv run mypy ralph/ --show-error-codes
```

#### Integration Tests Skipped

**Problem**: Integration tests show "skipped" in pytest output

**Solution**: By default, integration tests only run with stub tools. To test with real tools:
```bash
export RALPH_RUN_REAL_TOOL_TESTS=1
uv run pytest tests/test_ralph_integration.py
```

## Examples

### Example 1: Run amp for 5 iterations

```bash
$ uv run ralph --tool amp 5
ℹ️ Configuration loaded: tool=amp, max_iterations=5
ℹ️ ========== Iteration 1/5 ==========
# ... amp output ...
ℹ️ ========== Iteration 2/5 ==========
# ... amp output ...
✅ Detected completion signal!
```

### Example 2: Run codex with custom configuration

```bash
$ export CODEX_MODEL="gpt-4-turbo"
$ export CODEX_REASONING_EFFORT="medium"
$ uv run ralph --tool codex 10
ℹ️ Configuration loaded: tool=codex, max_iterations=10
ℹ️ ========== Iteration 1/10 ==========
# ... codex output ...
```

### Example 3: Using justfile

```bash
$ just ralph claude 3
uv run ralph --tool claude 3
ℹ️ Configuration loaded: tool=claude, max_iterations=3
# ... claude output ...
```

## Architecture

Ralph follows a functional programming approach using the `returns` library for error handling:

- **Result types**: All operations return `Result[T, Exception]` for explicit error handling
- **Maybe types**: Optional values use `Maybe[T]` (Some/Nothing)
- **No exceptions**: Errors are values, not control flow
- **Type safety**: `mypy --strict` ensures complete type coverage

### Key Abstractions

- **ToolExecutor Protocol**: Duck-typed interface for all tool executors
- **Result monad**: Explicit success/failure without exceptions
- **Functional configuration**: Immutable dataclass with factory methods

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run quality checks: `just ralph-all`
5. Commit your changes: `git commit -m "feat: add my feature"`
6. Push to the branch: `git push origin feature/my-feature`
7. Create a Pull Request

## License

See LICENSE file in the repository root.

## Version History

- **0.1.0**: Initial Python rewrite with amp/claude/codex support
