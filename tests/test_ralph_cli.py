"""Unit tests for Ralph CLI entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

import pytest

from ralph import entrypoint as ralph_cli


def test_main_requires_subcommand() -> None:
    """Test that main() requires a subcommand."""
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main([])
    assert exc_info.value.code == 2


def test_main_invalid_tool() -> None:
    """Test that main() rejects invalid tool names."""
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main(["run", "--tool", "invalid"])
    assert exc_info.value.code == 2


def test_main_version_flag() -> None:
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main(["--version"])
    assert exc_info.value.code == 0


def test_main_runs_with_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that main() executes with the run subcommand."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("# Test prompt\n")
    (tmp_path / ".taskmaster" / "tasks").mkdir(parents=True)
    (tmp_path / ".taskmaster" / "tasks" / "tasks.json").write_text(
        '{"tasks":[{"id":"task-001","title":"t","description":"d","status":"pending","priority":1}],"metadata":{"project":"t","branchName":"b","taskMasterVersion":"1.0"}}'
    )
    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(ralph_cli, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralph.entrypoint.time.sleep", lambda _seconds: None)

    exit_code = ralph_cli.main(["run", "--tool", "amp", "--max-iterations", "1"])

    assert exit_code == 0
    assert (tmp_path / "progress.txt").exists()


def test_main_defaults_to_sys_argv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test that main() defaults to sys.argv when no args provided."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("# Test prompt\n")
    (tmp_path / ".taskmaster" / "tasks").mkdir(parents=True)
    (tmp_path / ".taskmaster" / "tasks" / "tasks.json").write_text(
        '{"tasks":[{"id":"task-001","title":"t","description":"d","status":"pending","priority":1}],"metadata":{"project":"t","branchName":"b","taskMasterVersion":"1.0"}}'
    )
    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(ralph_cli, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralph.entrypoint.time.sleep", lambda _seconds: None)

    with patch.object(sys, "argv", ["ralph", "run", "--tool", "amp", "--max-iterations", "1"]):
        exit_code = ralph_cli.main()

    assert exit_code == 0
