from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from returns.result import Failure, Result, Success

from ralph.config import RalphConfig


class ToolExecutor(Protocol):
    """Protocol for tool executors."""

    def execute(self) -> Result[str, Exception]:
        """Execute the tool and return output."""
        ...


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _run_and_capture(
    cmd: list[str], stdin_path: Path | None = None
) -> Result[str, Exception]:
    """
    Run a subprocess command and capture output while streaming to stderr.

    Uses tee-like behavior: streams output to stderr while also capturing it.
    """
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

        if proc.returncode != 0:
            return Failure(
                Exception(f"Command failed with exit code {proc.returncode}")
            )

        return Success("".join(output_chunks))
    except Exception as exc:
        return Failure(exc)
    finally:
        if stdin is not None:
            stdin.close()


class AmpExecutor:
    """Executor for amp tool."""

    def __init__(self, config: RalphConfig) -> None:
        self.config = config

    def execute(self) -> Result[str, Exception]:
        """Execute amp with prompt.md from stdin."""
        root = _project_root()
        prompt_file = root / "prompt.md"
        return _run_and_capture(["amp", "--dangerously-allow-all"], stdin_path=prompt_file)


class ClaudeExecutor:
    """Executor for claude tool."""

    def __init__(self, config: RalphConfig) -> None:
        self.config = config

    def execute(self) -> Result[str, Exception]:
        """Execute claude with CLAUDE.md from stdin."""
        root = _project_root()
        claude_file = root / "CLAUDE.md"
        result = _run_and_capture(
            [
                "claude",
                "--model",
                "sonnet",
                "--dangerously-skip-permissions",
                "--print",
            ],
            stdin_path=claude_file,
        )
        # For claude, also write output to stdout
        if isinstance(result, Success):
            sys.stdout.write(result.unwrap())
        return result


class CodexExecutor:
    """Executor for codex tool."""

    def __init__(self, config: RalphConfig) -> None:
        self.config = config

    def execute(self) -> Result[str, Exception]:
        """Execute codex with configured parameters."""
        root = _project_root()
        codex_args = [
            "codex",
            "exec",
            "-m",
            self.config.codex_model,
            "--config",
            f'model_reasoning_effort="{self.config.codex_reasoning_effort}"',
            "--sandbox",
            self.config.codex_sandbox,
            "--dangerously-bypass-approvals-and-sandbox",
            "--cd",
            str(root),
        ]
        if self.config.codex_extra_args:
            codex_args.extend(shlex.split(self.config.codex_extra_args))
        codex_args.append("@ralph-next")
        return _run_and_capture(codex_args)


def create_executor(config: RalphConfig) -> ToolExecutor:
    """Create the appropriate executor based on config."""
    if config.tool == "amp":
        return AmpExecutor(config)
    elif config.tool == "claude":
        return ClaudeExecutor(config)
    elif config.tool == "codex":
        return CodexExecutor(config)
    else:
        raise ValueError(f"Unknown tool: {config.tool}")
