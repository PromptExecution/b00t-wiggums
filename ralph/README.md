# Ralph - Autonomous Coding Agent Loop Runner

Ralph is a Python CLI tool that runs AI coding agents (amp, claude, codex) in an iterative loop until they complete their tasks or reach a maximum iteration limit.

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

```bash
# Run with amp (default) for 10 iterations (default)
uv run ralph

# Run with claude for 5 iterations
uv run ralph --tool claude 5

# Run with codex for 20 iterations
uv run ralph --tool codex 20
```

### Using justfile Commands

The project includes convenient `just` commands:

```bash
# Run ralph with amp (default)
just ralph

# Run with specific tool
just ralph-claude
just ralph-codex
just ralph-amp

# Custom tool and iterations
just ralph claude 15
```

### Command-Line Options

```
usage: ralph [-h] [--tool {amp,claude,codex}] [--version] [max_iterations]

positional arguments:
  max_iterations        Maximum iterations to run (default: 10)

options:
  -h, --help            show this help message and exit
  --tool {amp,claude,codex}
                        Tool to run (default: amp)
  --version             show program's version number and exit
```

## How It Works

1. **Initialization**: Ralph reads `prd.json` and `progress.txt` from the project root
2. **Branch Detection**: Checks if git branch has changed since last run
3. **Archival**: If branch changed, archives previous run to `archive/{date}-{branch-name}/`
4. **Iteration Loop**: Runs the selected tool (amp/claude/codex) repeatedly
5. **Completion Detection**: Monitors tool output for `<promise>COMPLETE</promise>` signal
6. **Progress Tracking**: Updates `progress.txt` after each iteration

## Supported Tools

### amp
Runs `amp --dangerously-allow-all` reading from `prompt.md`

### claude
Runs `claude --model sonnet --dangerously-skip-permissions --print < CLAUDE.md`

### codex
Runs `codex exec` with full configuration (see Environment Variables below)

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

### Example: Custom Codex Configuration

```bash
export CODEX_MODEL="gpt-4-turbo"
export CODEX_REASONING_EFFORT="medium"
export CODEX_FULL_AUTO="false"
uv run ralph --tool codex 15
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
uv run ralph --tool amp 10
```

**Note**: The bash version now delegates to the Python version internally.

### Breaking Changes

- CLI flag changed: `--agent` → `--tool`
- Tool execution uses Python subprocess instead of direct bash execution
- Configuration is now centralized in `ralph/config.py`

## Project Structure

```
ralph/
├── __init__.py           # Package initialization
├── ralph_cli.py          # CLI entry point and argument parsing
├── config.py             # Configuration management
├── executors.py          # Tool execution (amp, claude, codex)
├── file_manager.py       # PRD and progress file operations
├── archiver.py           # Branch change detection and archival
├── runner.py             # Main iteration loop
└── logging_utils.py      # Logging utilities with emoji prefixes
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
