#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastmcp>=3.0.0b1",
# ]
# ///

import argparse
import datetime as _dt
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Ralph Wiggum 🎯")


def _warn_tool_deprecated():
    print("⚠️  Warning: --tool is deprecated, use --agent instead", file=sys.stderr)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ralph.sh",
        description="Ralph Wiggum - Long-running AI agent loop",
    )
    parser.add_argument("--agent", choices=("amp", "claude", "codex", "opencode"))
    parser.add_argument("--tool", choices=("amp", "claude", "codex", "opencode"), help=argparse.SUPPRESS)
    parser.add_argument("max_iterations", nargs="?", type=int, default=10)

    args = parser.parse_args(argv)

    if args.tool:
        _warn_tool_deprecated()
        if not args.agent:
            args.agent = args.tool

    if not args.agent:
        parser.error("--agent is required. Use --agent amp|claude|codex|opencode.")

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


def _find_git_root(start_path: Path) -> Path | None:
    """Find the git repository root directory."""
    current = start_path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def _verify_taskmaster_setup(git_root: Path) -> tuple[bool, str]:
    """
    Verify .taskmaster directory exists and is properly gitignored.

    Returns:
        (success: bool, message: str)
    """
    taskmaster_dir = git_root / ".taskmaster"
    gitignore_file = git_root / ".gitignore"

    # Check .taskmaster exists
    if not taskmaster_dir.exists():
        return False, f"TaskMaster directory not found: {taskmaster_dir}\nRun 'taskmaster init' first."

    # Check .gitignore exists and contains .taskmaster
    if not gitignore_file.exists():
        return False, f".gitignore not found at {gitignore_file}"

    gitignore_content = gitignore_file.read_text()
    if ".taskmaster" not in gitignore_content and ".taskmaster/" not in gitignore_content:
        return False, f".taskmaster/ not in .gitignore\nAdd '.taskmaster/' to {gitignore_file} for safety."

    return True, "TaskMaster setup verified ✓"


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    script_dir = Path(__file__).resolve().parent

    # Preflight: Verify TaskMaster setup
    git_root = _find_git_root(script_dir)
    if not git_root:
        print("Error: Not in a git repository", file=sys.stderr)
        return 1

    success, message = _verify_taskmaster_setup(git_root)
    print(f"TaskMaster preflight: {message}", file=sys.stderr)
    if not success:
        return 1

    progress_file = script_dir / "progress.txt"
    archive_dir = script_dir / "archive"
    last_branch_file = script_dir / ".last-branch"

    _codex_prompt_file = Path(
        os.environ.get("CODEX_PROMPT_FILE", str(script_dir / "prompt.md"))
    )
    codex_model = os.environ.get("CODEX_MODEL", "gpt-5.2-codex")
    codex_reasoning_effort = os.environ.get("CODEX_REASONING_EFFORT", "high")
    codex_sandbox = os.environ.get("CODEX_SANDBOX", "workspace-write")
    codex_extra_args = os.environ.get("CODEX_EXTRA_ARGS", "")

    # Note: Removed PRD handling - TaskMaster-AI now owns task storage
    _ensure_progress_file(progress_file)

    print(f"Starting Ralph - Agent: {args.agent} - Max iterations: {args.max_iterations}")

    for i in range(1, args.max_iterations + 1):
        print("")
        print("===============================================================")
        print(f"  Ralph Iteration {i} of {args.max_iterations} ({args.agent})")
        print("===============================================================")

        if args.agent == "amp":
            output = _run_and_capture(
                ["amp", "--dangerously-allow-all"],
                stdin_path=script_dir / "prompt.md",
            )
        elif args.agent == "codex":
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
                str(script_dir),
            ]
            if codex_extra_args:
                codex_args.extend(shlex.split(codex_extra_args))
            codex_args.append("@ralph-next")
            output = _run_and_capture(codex_args)
        else:
            output = _run_and_capture(
                [
                    "claude",
                    "--model",
                    "sonnet",
                    "--dangerously-skip-permissions",
                    "--print",
                ],
                stdin_path=script_dir / "CLAUDE.md",
            )
            sys.stdout.write(output)

        if "<promise>COMPLETE</promise>" in output:
            print("")
            print("Ralph completed all tasks!")
            print(f"Completed at iteration {i} of {args.max_iterations}")
            return 0

        print(f"Iteration {i} complete. Continuing...")
        time.sleep(2)

    print("")
    print(
        f"Ralph reached max iterations ({args.max_iterations}) without completing all tasks."
    )
    print(f"Check {progress_file} for status.")
    return 1


@mcp.tool()
def run_ralph_iteration(
    agent: str = "codex",
    max_iterations: int = 1,
) -> dict[str, str | int]:
    """
    Run Ralph autonomous agent for specified iterations.

    Note: Tasks are managed by TaskMaster-AI, not passed as parameters.

    Args:
        agent: Agent to use (amp, claude, codex, or opencode)
        max_iterations: Maximum number of iterations to run

    Returns:
        Status dict with exit_code and iterations_completed
    """
    args = ["--agent", agent, str(max_iterations)]

    exit_code = main(args)
    script_dir = Path(__file__).parent
    progress_file = script_dir / "progress.txt"

    return {
        "exit_code": exit_code,
        "status": "complete" if exit_code == 0 else "incomplete",
        "max_iterations": max_iterations,
        "progress_file": str(progress_file),
    }


@mcp.tool()
def get_ralph_status() -> dict[str, any]:
    """
    Get current Ralph execution status from progress.txt.
    
    Returns:
        Dict with latest progress information
    """
    script_dir = Path(__file__).parent
    progress_file = script_dir / "progress.txt"
    
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
def get_task_status() -> dict[str, any]:
    """
    Get TaskMaster story completion status via CLI.

    Note: This delegates to taskmaster-ai CLI, not direct file access.

    Returns:
        Dict with task metadata and story completion status
    """
    try:
        # Use taskmaster CLI to get status (respects separation of concerns)
        result = subprocess.run(
            ["taskmaster", "list", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        task_data = json.loads(result.stdout)

        total = len(task_data.get("tasks", []))
        completed = sum(1 for t in task_data["tasks"] if t.get("status") == "done")
        in_progress = sum(1 for t in task_data["tasks"] if t.get("status") == "in-progress")
        pending = sum(1 for t in task_data["tasks"] if t.get("status") == "pending")

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
    """
    Get current tasks via TaskMaster CLI (not direct file access).

    Returns task list as JSON string.
    """
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
    script_dir = Path(__file__).parent
    progress_file = script_dir / "progress.txt"
    
    if not progress_file.exists():
        return "No progress file found"
    
    return progress_file.read_text()


if __name__ == "__main__":
    # Check if running as MCP server or CLI
    if "--mcp" in sys.argv:
        sys.argv.remove("--mcp")
        mcp.run()
    else:
        raise SystemExit(main(sys.argv[1:]))
