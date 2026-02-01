"""Unit tests for Ralph CLI argument parsing."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from ralph.ralph_cli import main


def test_main_default_arguments() -> None:
    """Test main() with default arguments."""
    with (
        patch.object(sys, "argv", ["ralph"]),
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


def test_main_with_tool_argument() -> None:
    """Test main() with --tool argument."""
    with (
        patch.object(sys, "argv", ["ralph", "--tool", "codex"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    config = args[0][0]
    assert config.tool == "codex"


def test_main_with_max_iterations() -> None:
    """Test main() with positional max_iterations argument."""
    with (
        patch.object(sys, "argv", ["ralph", "5"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    max_iterations = args[0][1]
    assert max_iterations == 5


def test_main_with_tool_and_iterations() -> None:
    """Test main() with both --tool and max_iterations."""
    with (
        patch.object(sys, "argv", ["ralph", "--tool", "claude", "15"]),
        patch("ralph.runner.run_ralph", return_value=0) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 0
    args = mock_run.call_args
    config = args[0][0]
    max_iterations = args[0][1]
    assert config.tool == "claude"
    assert max_iterations == 15


def test_main_version_flag() -> None:
    """Test main() with --version flag."""
    with (
        patch.object(sys, "argv", ["ralph", "--version"]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 0


def test_main_invalid_tool() -> None:
    """Test main() with invalid tool choice."""
    with (
        patch.object(sys, "argv", ["ralph", "--tool", "invalid"]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 2


def test_main_returns_nonzero_on_failure() -> None:
    """Test main() returns non-zero exit code on failure."""
    with (
        patch.object(sys, "argv", ["ralph"]),
        patch("ralph.runner.run_ralph", return_value=1) as mock_run,
    ):
        exit_code = main()

    assert exit_code == 1
