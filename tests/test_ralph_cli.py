"""Unit tests for Ralph CLI entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

import pytest

from ralph import ralph_cli


def test_main_requires_agent() -> None:
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main([])
    assert exc_info.value.code == 2


def test_main_invalid_agent() -> None:
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main(["--agent", "invalid"])
    assert exc_info.value.code == 2


def test_main_version_flag() -> None:
    with pytest.raises(SystemExit) as exc_info:
        ralph_cli.main(["--version"])
    assert exc_info.value.code == 0


def test_main_runs_with_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "prompt.md").write_text("# Test prompt\n")
    monkeypatch.setattr(ralph_cli, "__file__", str(tmp_path / "ralphython.py"))

    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(ralph_cli, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralph.ralph_cli.time.sleep", lambda _seconds: None)

    exit_code = ralph_cli.main(["--agent", "amp", "1"])

    assert exit_code == 0
    assert (tmp_path / "progress.txt").exists()


def test_main_defaults_to_sys_argv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "prompt.md").write_text("# Test prompt\n")
    monkeypatch.setattr(ralph_cli, "__file__", str(tmp_path / "ralphython.py"))

    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(ralph_cli, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralph.ralph_cli.time.sleep", lambda _seconds: None)

    with patch.object(sys, "argv", ["ralph", "--agent", "amp", "1"]):
        exit_code = ralph_cli.main()

    assert exit_code == 0
