"""Unit tests for Ralph CLI argument parsing and subcommands."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from ralph.ralph_cli import main


def test_main_no_subcommand_shows_help() -> None:
    """Test main() with no subcommand shows help and exits gracefully."""
    from io import StringIO

    with (
        patch.object(sys, "argv", ["ralph"]),
        patch.object(sys, "stdout", new_callable=StringIO) as mock_stdout,
    ):
        exit_code = main()

    assert exit_code == 0
    # Help text should be printed to stdout
    output = mock_stdout.getvalue()
    assert "Ralph - Autonomous coding agent loop runner" in output
    assert "run" in output
    assert "status" in output
    assert "list-tasks" in output


def test_main_run_default_arguments() -> None:
    """Test main() run subcommand with default arguments."""
    with (
        patch.object(sys, "argv", ["ralph", "run"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    mock_run.assert_called_once()
    args = mock_run.call_args
    config = args[0][0]
    max_iterations = args[0][1]
    assert config.tool == "amp"
    assert max_iterations == 10


def test_main_run_with_agent_argument() -> None:
    """Test main() run subcommand with --agent argument."""
    with (
        patch.object(sys, "argv", ["ralph", "run", "--agent", "codex"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    config = args[0][0]
    assert config.tool == "codex"


def test_main_run_with_max_iterations() -> None:
    """Test main() run subcommand with --max-iterations argument."""
    with (
        patch.object(sys, "argv", ["ralph", "run", "--max-iterations", "5"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    max_iterations = args[0][1]
    assert max_iterations == 5


def test_main_run_with_agent_and_iterations() -> None:
    """Test main() run subcommand with both --agent and --max-iterations."""
    with (
        patch.object(sys, "argv", ["ralph", "run", "--agent", "claude", "--max-iterations", "15"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    config = args[0][0]
    max_iterations = args[0][1]
    assert config.tool == "claude"
    assert max_iterations == 15


def test_main_run_with_opencode() -> None:
    """Test main() run subcommand with opencode agent."""
    with (
        patch.object(sys, "argv", ["ralph", "run", "--agent", "opencode"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    config = args[0][0]
    assert config.tool == "opencode"


def test_main_version_flag() -> None:
    """Test main() with --version flag."""
    with (
        patch.object(sys, "argv", ["ralph", "--version"]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 0


def test_main_run_invalid_agent() -> None:
    """Test main() run subcommand with invalid agent choice."""
    with (
        patch.object(sys, "argv", ["ralph", "run", "--agent", "invalid"]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 2


def test_main_run_returns_nonzero_on_failure() -> None:
    """Test main() run subcommand returns non-zero exit code on failure."""
    with (
        patch.object(sys, "argv", ["ralph", "run"]),
        patch("ralph.runner.run_ralph", return_value=1) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 1


def test_main_status_command() -> None:
    """Test main() status subcommand."""
    mock_task = MagicMock()
    mock_task.status = "done"
    mock_task.blocked_by = []

    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.unwrap.return_value = [mock_task, mock_task, mock_task]
    mock_client.get_all_tasks.return_value = mock_result

    with (
        patch.object(sys, "argv", ["ralph", "status"]),
        patch("ralph.taskmaster_adapter.create_client", return_value=mock_client),
        patch("builtins.print") as mock_print,
    ):
        exit_code = main()

    assert exit_code == 0
    assert mock_print.called
    # Verify status output was printed
    output = "".join(str(call) for call in mock_print.call_args_list)
    assert "Total Tasks" in output


def test_main_list_tasks_command() -> None:
    """Test main() list-tasks subcommand."""
    mock_task = MagicMock()
    mock_task.id = "task-001"
    mock_task.title = "Test Task"
    mock_task.status = "pending"
    mock_task.priority = 1
    mock_task.blocked_by = []

    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.unwrap.return_value = [mock_task]
    mock_client.get_all_tasks.return_value = mock_result

    with (
        patch.object(sys, "argv", ["ralph", "list-tasks"]),
        patch("ralph.taskmaster_adapter.create_client", return_value=mock_client),
        patch("builtins.print") as mock_print,
    ):
        exit_code = main()

    assert exit_code == 0
    assert mock_print.called


def test_main_list_tasks_with_filter() -> None:
    """Test main() list-tasks subcommand with filter."""
    mock_task_pending = MagicMock()
    mock_task_pending.id = "task-001"
    mock_task_pending.title = "Pending Task"
    mock_task_pending.status = "pending"
    mock_task_pending.priority = 1
    mock_task_pending.blocked_by = []

    mock_task_done = MagicMock()
    mock_task_done.id = "task-002"
    mock_task_done.title = "Done Task"
    mock_task_done.status = "done"
    mock_task_done.priority = 2
    mock_task_done.blocked_by = []

    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.unwrap.return_value = [mock_task_pending, mock_task_done]
    mock_client.get_all_tasks.return_value = mock_result

    with (
        patch.object(sys, "argv", ["ralph", "list-tasks", "--filter", "pending"]),
        patch("ralph.taskmaster_adapter.create_client", return_value=mock_client),
        patch("builtins.print") as mock_print,
    ):
        exit_code = main()

    assert exit_code == 0
    # Verify that only pending task appears in output
    output = "".join(str(call) for call in mock_print.call_args_list)
    assert "Pending Task" in output
    assert "Done Task" not in output
