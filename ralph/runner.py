"""Iteration runner for Ralph automation."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TypeVar

from returns.result import Failure, Result

from ralph.config import RalphConfig
from ralph.executors import AmpExecutor, ClaudeExecutor, CodexExecutor, ToolExecutor
from ralph.logging_utils import (
    configure_logging,
    log_error,
    log_info,
    log_success,
    log_warning,
)
from ralph.taskmaster_adapter import create_client

WORKING_DIR = Path.cwd()
PROMPT_FILE = WORKING_DIR / "prompt.md"
CLAUDE_PROMPT_FILE = WORKING_DIR / "CLAUDE.md"
COMPLETE_MARKER = "<promise>COMPLETE</promise>"
ResultValue = TypeVar("ResultValue")


def _unwrap_result(result: Result[ResultValue, Exception], message: str) -> ResultValue:
    """Unwrap a Result or raise a chained error."""

    if isinstance(result, Failure):
        error = result.failure()
        raise RuntimeError(message) from error
    return result.unwrap()


def _check_for_completion(output: str) -> bool:
    """Check if the output contains the completion marker."""
    return COMPLETE_MARKER in output


def _build_executor(tool: str, config: RalphConfig) -> ToolExecutor:
    """Create the executor for the selected tool."""

    match tool:
        case "amp":
            return AmpExecutor(prompt_path=PROMPT_FILE, working_dir=WORKING_DIR)
        case "claude":
            return ClaudeExecutor(prompt_path=CLAUDE_PROMPT_FILE, working_dir=WORKING_DIR)
        case "codex":
            return CodexExecutor(config=config, working_dir=WORKING_DIR)
    raise ValueError(f"Unsupported tool requested: {tool}")


def run_ralph(config: RalphConfig, max_iterations: int) -> int:
    """Run the Ralph tool loop for a maximum number of iterations."""

    logger = configure_logging()

    log_info(
        logger,
        f"Configuration loaded: tool={config.tool} iterations={max_iterations} model={config.codex_model}",
    )

    # Create TaskMaster client for progress tracking
    # Note: TaskMaster finds tasks in .taskmaster/ (set up by ralph.sh)
    taskmaster = create_client(
        prefer_mcp=config.use_mcp,
        mcp_url=config.taskmaster_url,
    )

    # Display initial task summary
    tasks_result = taskmaster.get_all_tasks()
    if isinstance(tasks_result, Failure):
        log_warning(logger, f"Could not load tasks: {tasks_result.failure()}")
    else:
        tasks = tasks_result.unwrap()
        pending = [t for t in tasks if t.status == "pending"]
        in_progress = [t for t in tasks if t.status == "in-progress"]
        done = [t for t in tasks if t.status == "done"]
        log_info(logger, f"Tasks: {len(done)} done, {len(in_progress)} in progress, {len(pending)} pending")

    executor = _build_executor(config.tool, config)

    for iteration in range(1, max_iterations + 1):
        log_info(logger, "")
        log_info(logger, "=" * 63)
        log_info(logger, f"Ralph Iteration {iteration} of {max_iterations} ({config.tool})")
        log_info(logger, "=" * 63)

        try:
            output = _unwrap_result(executor.run(), "Tool execution failed")
        except RuntimeError as exc:
            log_error(logger, "Tool execution failed", exc)
            return 1

        if _check_for_completion(output):
            log_info(logger, "")
            log_success(logger, "Ralph completed all tasks!")
            log_success(logger, f"Completed at iteration {iteration} of {max_iterations}")

            # Display final task summary
            tasks_result = taskmaster.get_all_tasks()
            if not isinstance(tasks_result, Failure):
                tasks = tasks_result.unwrap()
                done = [t for t in tasks if t.status == "done"]
                log_success(logger, f"Final: {len(done)}/{len(tasks)} tasks completed")
            return 0

        log_info(logger, f"Iteration {iteration} complete. Continuing...")
        time.sleep(2)

    log_info(logger, "")
    log_warning(
        logger,
        f"Ralph reached max iterations ({max_iterations}) without completing all tasks.",
    )
    return 1


__all__ = ["run_ralph"]
