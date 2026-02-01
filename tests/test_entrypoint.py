from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pytest

from ralph import entrypoint


def test_parse_args_requires_agent() -> None:
    with pytest.raises(SystemExit) as exc:
        entrypoint._parse_args([])
    assert exc.value.code == 2


def test_parse_args_valid_agent() -> None:
    args = entrypoint._parse_args(["--agent", "amp", "3"])
    assert args.agent == "amp"
    assert args.max_iterations == 3


def test_progress_file_created_on_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("# Test prompt\n")
    (tmp_path / ".taskmaster" / "tasks").mkdir(parents=True)
    (tmp_path / ".taskmaster" / "tasks" / "tasks.json").write_text(
        '{"tasks":[{"id":"task-001","title":"t","description":"d","status":"pending","priority":1}],"metadata":{"project":"t","branchName":"b","taskMasterVersion":"1.0"}}'
    )

    def fake_run(_cmd: Sequence[str], stdin_path: Path | None = None) -> str:
        return "<promise>COMPLETE</promise>"

    monkeypatch.setattr(entrypoint, "_run_and_capture", fake_run)
    monkeypatch.setattr("ralph.entrypoint.time.sleep", lambda _seconds: None)

    rc = entrypoint.main(["--agent", "amp", "1"])
    assert rc == 0
    assert (tmp_path / "progress.txt").exists()
