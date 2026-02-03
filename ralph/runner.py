"""Iteration runner for Ralph automation."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TypeVar

from returns.result import Failure, Result

from ralph.budget_guardian import (
    BudgetConfig,
    BudgetGuardian,
    EscalationLevel,
)
from ralph.config import RalphConfig
from ralph.executors import (
    AmpExecutor,
    ClaudeExecutor,
    CodexExecutor,
    OpenCodeExecutor,
    ToolExecutor,
)
from ralph.logging_utils import (
    configure_logging,
    log_error,
    log_info,
    log_success,
    log_warning,
)
from ralph.progress_display import display_progress_summary
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
        case "opencode":
            return OpenCodeExecutor(
                prompt_path=PROMPT_FILE,
                working_dir=WORKING_DIR,
                model=config.opencode_model,
                extra_args=config.opencode_extra_args,
            )
    raise ValueError(f"Unsupported tool requested: {tool}")


def _create_budget_guardian(
    config: RalphConfig, logger: logging.Logger
) -> BudgetGuardian | None:
    """Create a budget guardian from config if enabled."""
    if not config.budget_enabled:
        return None

    def escalation_callback(level: EscalationLevel, _state: object) -> None:
        """Callback for escalation level changes."""
        if level == EscalationLevel.WARNING:
            log_warning(logger, f"🚨 Officer Clancy: Budget warning - {level.value} level")
        elif level == EscalationLevel.CRITICAL:
            log_warning(logger, "🚨 Officer Clancy: CRITICAL - approaching budget limit")
        elif level == EscalationLevel.EXCEEDED:
            log_error(logger, "🚨 Officer Clancy: BUDGET EXCEEDED - stopping execution")

    budget_config = BudgetConfig(
        max_attempts=config.budget_max_attempts,
        budget_limit=config.budget_limit,
        cost_per_attempt=config.budget_cost_per_attempt,
        allow_budget_overflow=config.budget_allow_overflow,
    )

    return BudgetGuardian(budget_config, escalation_callback=escalation_callback)


def run_ralph(config: RalphConfig, max_iterations: int) -> int:
    """Run the Ralph tool loop for a maximum number of iterations."""

    logger = configure_logging()

    log_info(
        logger,
        f"Configuration loaded: tool={config.tool} iterations={max_iterations} model={config.codex_model}",
    )

    # Initialize Officer Clancy Budget Guardian
    guardian = _create_budget_guardian(config, logger)
    if guardian is not None:
        log_info(
            logger,
            f"🚨 Officer Clancy on duty: max_attempts={config.budget_max_attempts}, "
            f"budget={config.budget_limit:.2f}",
        )

    # Create TaskMaster client for progress tracking
    # Note: TaskMaster finds tasks in .taskmaster/ (set up by ralph.sh)
    taskmaster = create_client(
        prefer_mcp=config.use_mcp,
        mcp_url=config.taskmaster_url,
    )

    # Display initial task summary with visual progress
    tasks_result = taskmaster.get_all_tasks()
    if isinstance(tasks_result, Failure):
        log_warning(logger, f"Could not load tasks: {tasks_result.failure()}")
    else:
        tasks = tasks_result.unwrap()
        summary = display_progress_summary(tasks)
        log_info(logger, "\n" + summary)

    executor = _build_executor(config.tool, config)

    for iteration in range(1, max_iterations + 1):
        # Check with Officer Clancy before each iteration
        if guardian is not None:
            attempt_result = guardian.authorize_attempt()
            if isinstance(attempt_result, Failure):
                error = attempt_result.failure()
                log_error(logger, f"🚨 Officer Clancy: {error}")
                log_info(logger, guardian.get_summary())
                return 1
            attempt = attempt_result.unwrap()
            log_info(
                logger,
                f"🚨 Officer Clancy: Attempt {attempt.attempt_number} authorized "
                f"(budget: {attempt.remaining_budget:.2f}/{config.budget_limit:.2f})",
            )

        log_info(logger, "")
        log_info(logger, "=" * 63)
        log_info(logger, f"Ralph Iteration {iteration} of {max_iterations} ({config.tool})")
        log_info(logger, "=" * 63)

        try:
            output = _unwrap_result(executor.run(), "Tool execution failed")
            if guardian is not None:
                guardian.record_success()
        except RuntimeError as exc:
            log_error(logger, "Tool execution failed", exc)
            if guardian is not None:
                guardian.record_failure(str(exc))
                log_info(logger, guardian.get_summary())
            return 1

        if _check_for_completion(output):
            log_info(logger, "")
            log_success(logger, "Ralph completed all tasks!")
            log_success(logger, f"Completed at iteration {iteration} of {max_iterations}")

            # Display Officer Clancy final report
            if guardian is not None:
                log_success(logger, guardian.get_summary())

            # Display final task summary with visual progress
            tasks_result = taskmaster.get_all_tasks()
            if not isinstance(tasks_result, Failure):
                tasks = tasks_result.unwrap()
                summary = display_progress_summary(tasks)
                log_success(logger, "\n" + summary)
            return 0

        log_info(logger, f"Iteration {iteration} complete. Continuing...")
        time.sleep(2)

    log_info(logger, "")
    log_warning(
        logger,
        f"Ralph reached max iterations ({max_iterations}) without completing all tasks.",
    )
    if guardian is not None:
        log_info(logger, guardian.get_summary())
    return 1


__all__ = ["run_ralph"]
