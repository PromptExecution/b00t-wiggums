from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Keep the MCP surface area close to the runtime implementation so there is
# a single source of truth for "how Ralph runs".
mcp = FastMCP("Ralph Wiggum 🎯")

logging.basicConfig(level=logging.INFO, format="%(message)s")
LOGGER = logging.getLogger("ralph")

__version__ = "0.1.0"


def _project_root() -> Path:
    # Prefer the git root of the current working directory so `ralph` can be used
    # as a tool against *any* repo, not just this package's source checkout.
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").is_dir():
            return candidate
    return cwd


def _tasks_file(root: Path) -> Path:
    return root / ".taskmaster" / "tasks" / "tasks.json"


def _print_tasks_missing_instructions() -> None:
    # Keep this short and copy/paste friendly. It is printed from both bash and python
    # entrypoints to keep behavior consistent regardless of invocation method.
    sys.stderr.write("\n")
    sys.stderr.write("To create tasks with the prd skill, run your designated agent with this prompt:\n\n")
    sys.stderr.write(
        "Use the prd skill to generate TaskMaster tasks.json for this repo.\n"
        "Requirements:\n"
        "- Output must be TaskMaster format with tasks[] and metadata.\n"
        "- Include 3-7 small, actionable tasks with acceptance criteria.\n"
        "- Use IETF 2119 MUST/SHOULD/MAY in acceptance criteria.\n"
        "- Set metadata.project and metadata.branchName appropriately.\n"
    )
    sys.stderr.write("\nThen re-run: ./ralph.sh --agent <amp|claude|codex> [max_iterations]\n\n")


def _require_tasks(root: Path) -> bool:
    """Return True if tasks exist and are non-empty; otherwise print instructions and return False."""
    tasks_path = _tasks_file(root)
    if not tasks_path.exists():
        LOGGER.warning("TaskMaster tasks.json not found; nothing to do.")
        _print_tasks_missing_instructions()
        return False

    try:
        payload = json.loads(tasks_path.read_text())
    except json.JSONDecodeError:
        LOGGER.warning("TaskMaster tasks.json is invalid JSON; nothing to do.")
        _print_tasks_missing_instructions()
        return False

    tasks = payload.get("tasks") if isinstance(payload, dict) else None
    if not tasks:
        LOGGER.warning("TaskMaster tasks.json is empty; nothing to do.")
        _print_tasks_missing_instructions()
        return False

    return True


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph Wiggum - Long-running AI agent loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Claude agent for max 10 iterations
  ralph run --tool claude --max-iterations 10

  # Run with OpenCode agent using a specific task
  ralph run --tool opencode --task-id task-003

  # Dry-run mode (show what would happen without executing)
  ralph run --tool amp --dry-run

  # Show current task status
  ralph status

  # List all tasks
  ralph list-tasks

  # List only pending tasks
  ralph list-tasks --filter pending

  # Run as MCP server
  ralph --mcp
        """,
    )

    # Global flags
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as an MCP server (ignores subcommands)",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host when using --transport http (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port when using --transport http (default: 8000)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Execute the agent loop",
        description="Run Ralph autonomous agent for specified iterations",
    )
    run_parser.add_argument(
        "--tool",
        required=True,
        choices=("amp", "claude", "codex", "opencode"),
        help="AI tool to use for execution",
    )
    run_parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations to run (default: 10)",
    )
    run_parser.add_argument(
        "--task-id",
        type=str,
        help="Specific task ID to execute (optional)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing",
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    # Status subcommand
    subparsers.add_parser(
        "status",
        help="Show current task status summary",
        description="Display TaskMaster completion status and progress",
    )

    # List-tasks subcommand
    list_tasks_parser = subparsers.add_parser(
        "list-tasks",
        help="List all stories",
        description="Display all tasks with optional filtering",
    )
    list_tasks_parser.add_argument(
        "--filter",
        choices=("all", "pending", "in-progress", "done"),
        default="all",
        help="Filter tasks by status (default: all)",
    )

    # Backwards compatibility: if no subcommand but --agent is provided
    args = parser.parse_args(argv)

    # Handle MCP mode
    if args.mcp:
        return args

    # Handle backwards compatibility: --agent flag without subcommand
    if hasattr(args, 'command') and args.command is None:
        # Check if old-style flags were used
        if '--agent' in argv or any(arg in argv for arg in ('amp', 'claude', 'codex', 'opencode')):
            parser.error(
                "The --agent flag is deprecated. Use subcommands instead:\n"
                "  ralph run --tool amp|claude|codex|opencode [--max-iterations N]"
            )
        parser.error(
            "A subcommand is required. Use 'ralph run', 'ralph status', or 'ralph list-tasks'.\n"
            "Run 'ralph --help' for more information."
        )

    return args


def _ensure_progress_file(progress_file: Path) -> None:
    if progress_file.exists():
        return
    progress_file.write_text(
        "# Ralph Progress Log\n"
        f"Started: {_dt.datetime.now()}\n"
        "---\n"
    )


def _run_and_capture(cmd: list[str], stdin_path: Path | None = None) -> str:
    stdin = None
    try:
        if stdin_path is not None:
            stdin = stdin_path.open("r")
        proc = subprocess.Popen(
            cmd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        output_chunks: list[str] = []
        for line in proc.stdout:
            sys.stderr.write(line)
            output_chunks.append(line)
        proc.wait()
        return "".join(output_chunks)
    finally:
        if stdin is not None:
            stdin.close()


def _cmd_run(args: argparse.Namespace, root: Path) -> int:
    """Execute the agent loop (run subcommand)."""
    if not _require_tasks(root):
        return 1

    progress_file = root / "progress.txt"
    _ensure_progress_file(progress_file)

    if args.dry_run:
        LOGGER.info("DRY RUN MODE - No actual execution")
        LOGGER.info("Tool: %s", args.tool)
        LOGGER.info("Max iterations: %s", args.max_iterations)
        if args.task_id:
            LOGGER.info("Task ID: %s", args.task_id)
        LOGGER.info("Would execute agent loop but exiting due to --dry-run")
        return 0

    # Environment variables for codex
    codex_model = os.environ.get("CODEX_MODEL", "gpt-5.2-codex")
    codex_reasoning_effort = os.environ.get("CODEX_REASONING_EFFORT", "high")
    codex_sandbox = os.environ.get("CODEX_SANDBOX", "workspace-write")
    codex_extra_args = os.environ.get("CODEX_EXTRA_ARGS", "")

    log_level = "verbose" if args.verbose else "normal"
    LOGGER.info(
        "Starting Ralph - Tool: %s - Max iterations: %s - Log level: %s",
        args.tool,
        args.max_iterations,
        log_level,
    )
    if args.task_id:
        LOGGER.info("Targeting specific task: %s", args.task_id)

    for i in range(1, args.max_iterations + 1):
        LOGGER.info("")
        LOGGER.info("===============================================================")
        LOGGER.info("  Ralph Iteration %s of %s (%s)", i, args.max_iterations, args.tool)
        LOGGER.info("===============================================================")

        if args.tool == "amp":
            output = _run_and_capture(
                ["amp", "--dangerously-allow-all"],
                stdin_path=root / "prompt.md",
            )
        elif args.tool == "codex":
            codex_args = [
                "codex",
                "exec",
                "-m",
                codex_model,
                "--config",
                f"model_reasoning_effort=\"{codex_reasoning_effort}\"",
                "--sandbox",
                codex_sandbox,
                "--dangerously-bypass-approvals-and-sandbox",
                "--cd",
                str(root),
            ]
            if codex_extra_args:
                codex_args.extend(shlex.split(codex_extra_args))
            codex_args.append("@ralph-next")
            output = _run_and_capture(codex_args)
        elif args.tool == "opencode":
            # OpenCode executor (placeholder - adjust CLI as needed)
            output = _run_and_capture(
                ["opencode", "--model", "default"],
                stdin_path=root / "CLAUDE.md",
            )
        else:  # claude
            output = _run_and_capture(
                [
                    "claude",
                    "--model",
                    "sonnet",
                    "--dangerously-skip-permissions",
                    "--print",
                ],
                stdin_path=root / "CLAUDE.md",
            )

        if "<promise>COMPLETE</promise>" in output:
            LOGGER.info("")
            LOGGER.info("Ralph completed all tasks!")
            LOGGER.info("Completed at iteration %s of %s", i, args.max_iterations)
            return 0

        LOGGER.info("Iteration %s complete. Continuing...", i)
        time.sleep(2)

    LOGGER.info("")
    LOGGER.info(
        "Ralph reached max iterations (%s) without completing all tasks.",
        args.max_iterations,
    )
    LOGGER.info("Check %s for status.", progress_file)
    return 1


def _cmd_status(_args: argparse.Namespace, _root: Path) -> int:
    """Show current task status summary (status subcommand)."""
    try:
        result = subprocess.run(
            ["taskmaster", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        tasks = data.get("tasks", [])
        metadata = data.get("metadata", {})

        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "done")
        in_progress = sum(1 for t in tasks if t.get("status") == "in-progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        blocked = sum(1 for t in tasks if t.get("blockedBy", []))

        completion_pct = round((completed / total) * 100, 1) if total > 0 else 0

        print(f"\n{'=' * 60}")
        print(f"Project: {metadata.get('project', 'Unknown')}")
        print(f"Branch: {metadata.get('branchName', 'Unknown')}")
        print(f"{'=' * 60}")
        print(f"\nProgress: {completion_pct}% complete")
        print(f"  ✓ Completed: {completed}/{total}")
        print(f"  ⚡ In Progress: {in_progress}")
        print(f"  ○ Pending: {pending}")
        print(f"  🚫 Blocked: {blocked}")
        print(f"{'=' * 60}\n")

        return 0
    except subprocess.CalledProcessError as e:
        LOGGER.error("Failed to get task status: %s", e.stderr)
        return 1
    except FileNotFoundError:
        LOGGER.error("taskmaster CLI not found. Install taskmaster-ai first.")
        return 1
    except Exception as e:
        LOGGER.error("Error getting task status: %s", e)
        return 1


def _cmd_list_tasks(args: argparse.Namespace, _root: Path) -> int:
    """List all tasks with optional filtering (list-tasks subcommand)."""
    try:
        result = subprocess.run(
            ["taskmaster", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        tasks = data.get("tasks", [])

        # Apply filter
        if args.filter != "all":
            tasks = [t for t in tasks if t.get("status") == args.filter]

        if not tasks:
            print(f"\nNo tasks found with filter: {args.filter}\n")
            return 0

        print(f"\n{'=' * 60}")
        print(f"Tasks (filter: {args.filter})")
        print(f"{'=' * 60}\n")

        for task in tasks:
            status_emoji = {
                "done": "✓",
                "in-progress": "⚡",
                "pending": "○",
                "cancelled": "✗",
            }.get(task.get("status", "pending"), "○")

            blocked_marker = " 🚫" if task.get("blockedBy", []) else ""
            priority = task.get("priority", 0)

            print(f"{status_emoji} [{task.get('id')}] {task.get('title')}{blocked_marker}")
            print(f"   Priority: {priority} | Status: {task.get('status')}")

            if task.get("blockedBy"):
                print(f"   Blocked by: {', '.join(task.get('blockedBy', []))}")

            print()

        print(f"{'=' * 60}\n")
        return 0
    except subprocess.CalledProcessError as e:
        LOGGER.error("Failed to list tasks: %s", e.stderr)
        return 1
    except FileNotFoundError:
        LOGGER.error("taskmaster CLI not found. Install taskmaster-ai first.")
        return 1
    except Exception as e:
        LOGGER.error("Error listing tasks: %s", e)
        return 1


def main(argv: list[str] | None = None) -> int:
    """
    Ralph runtime execution.

    Note: Preflight checks (uv sync, .taskmaster setup, .gitignore) are handled
    by ralph.sh wrapper. This function focuses on execution only.
    """
    if argv is None:
        argv = sys.argv[1:]

    args = _parse_args(argv)
    root = _project_root()

    # Handle MCP mode
    if args.mcp:
        if args.transport == "http":
            mcp.run(transport="http", host=args.host, port=args.port)
        else:
            mcp.run(transport="stdio")
        return 0

    # Dispatch to subcommand handlers
    if args.command == "run":
        return _cmd_run(args, root)
    elif args.command == "status":
        return _cmd_status(args, root)
    elif args.command == "list-tasks":
        return _cmd_list_tasks(args, root)

    # Should never reach here due to argparse validation
    LOGGER.error("Unknown command: %s", args.command)
    return 1


@mcp.tool()
def run_ralph_iteration(
    tool: str = "codex",
    max_iterations: int = 1,
    task_id: str | None = None,
) -> dict[str, str | int]:
    """Run Ralph autonomous agent for specified iterations."""
    args = ["run", "--tool", tool, "--max-iterations", str(max_iterations)]
    if task_id:
        args.extend(["--task-id", task_id])

    exit_code = main(args)
    root = _project_root()
    progress_file = root / "progress.txt"

    return {
        "exit_code": exit_code,
        "status": "complete" if exit_code == 0 else "incomplete",
        "max_iterations": max_iterations,
        "progress_file": str(progress_file),
    }


@mcp.tool()
def get_ralph_status() -> dict[str, Any]:
    """Get current Ralph execution status from progress.txt."""
    root = _project_root()
    progress_file = root / "progress.txt"

    if not progress_file.exists():
        return {"status": "no_progress_file", "message": "No progress.txt found"}

    content = progress_file.read_text()
    lines = content.strip().split("\n")

    return {
        "status": "active",
        "progress_file": str(progress_file),
        "last_lines": lines[-10:] if len(lines) > 10 else lines,
        "total_lines": len(lines),
    }


@mcp.tool()
def get_task_status() -> dict[str, Any]:
    """Get TaskMaster completion status via taskmaster CLI."""
    try:
        result = subprocess.run(
            ["taskmaster", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        task_data = json.loads(result.stdout)

        total = len(task_data.get("tasks", []))
        completed = sum(1 for t in task_data.get("tasks", []) if t.get("status") == "done")
        in_progress = sum(1 for t in task_data.get("tasks", []) if t.get("status") == "in-progress")
        pending = sum(1 for t in task_data.get("tasks", []) if t.get("status") == "pending")

        return {
            "status": "loaded",
            "project": task_data.get("metadata", {}).get("project", "Unknown"),
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percentage": round((completed / total) * 100, 1) if total > 0 else 0,
        }
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"taskmaster CLI error: {e}"}
    except FileNotFoundError:
        return {"status": "error", "message": "taskmaster CLI not found. Install taskmaster-ai first."}


@mcp.resource("ralph://tasks")
def get_tasks_resource() -> str:
    """Get current tasks via taskmaster CLI (not direct file access)."""
    try:
        result = subprocess.run(
            ["taskmaster", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return json.dumps({"error": "Failed to fetch tasks from taskmaster"})
    except FileNotFoundError:
        return json.dumps({"error": "taskmaster CLI not found"})


@mcp.resource("ralph://progress")
def get_progress_resource() -> str:
    """Get the current progress log as a resource."""
    root = _project_root()
    progress_file = root / "progress.txt"

    if not progress_file.exists():
        return "No progress file found"

    return progress_file.read_text()
