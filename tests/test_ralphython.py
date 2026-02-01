from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest
from _pytest.monkeypatch import MonkeyPatch

import ralphython


def test_parse_args_requires_agent() -> None:
    with pytest.raises(SystemExit) as exc:
        ralphython._parse_args([])
    assert exc.value.code == 2


def test_parse_args_valid_agent() -> None:
    args = ralphython._parse_args(["--agent", "amp", "3"])
    assert args.agent == "amp"
    assert args.max_iterations == 3


def test_progress_file_created_on_run(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "prompt.md").write_text("# Test prompt\n")

    monkeypatch.setattr(ralphython, "__file__", str(tmp_path / "ralphython.py"))

    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(ralphython, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralphython.time.sleep", lambda _seconds: None)

    rc = ralphython.main(["--agent", "amp", "1"])
    assert rc == 0
    progress_path = tmp_path / "progress.txt"
    assert progress_path.exists()
