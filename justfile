# Ralph Python CLI justfile commands

# Run ralph with specified tool and iterations (default: amp, 10 iterations)
ralph TOOL='amp' ITERATIONS='10':
    uv run ralph --tool {{TOOL}} {{ITERATIONS}}

# Run ralph tests
ralph-test:
    uv run pytest tests/test_ralph*

# Type check and lint ralph module
ralph-check:
    uv run mypy ralph/ && uv run ruff check ralph/

# Format ralph code with ruff
ralph-format:
    uv run ruff format ralph/

# Run all quality checks (format, lint, type check, test)
ralph-all: ralph-format ralph-check ralph-test
    @echo "✅ All quality checks passed!"

# Run ralph with amp tool
ralph-amp ITERATIONS='10':
    uv run ralph --tool amp {{ITERATIONS}}

# Run ralph with claude tool
ralph-claude ITERATIONS='10':
    uv run ralph --tool claude {{ITERATIONS}}

# Run ralph with codex tool
ralph-codex ITERATIONS='10':
    uv run ralph --tool codex {{ITERATIONS}}
