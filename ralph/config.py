from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class RalphConfig:
    """Configuration for Ralph tool execution."""

    # Tool selection
    tool: str  # amp, claude, or codex

    # Codex-specific configuration
    codex_prompt_file: Path
    codex_model: str
    codex_reasoning_effort: str
    codex_sandbox: str
    codex_full_auto: bool
    codex_extra_args: str

    @classmethod
    def from_env(cls, tool: str = "amp") -> RalphConfig:
        """Load configuration from environment variables with defaults."""
        root = _project_root()
        return cls(
            tool=tool,
            codex_prompt_file=Path(os.environ.get("CODEX_PROMPT_FILE", str(root / "CLAUDE.md"))),
            codex_model=os.environ.get("CODEX_MODEL", "gpt-5-codex"),
            codex_reasoning_effort=os.environ.get("CODEX_REASONING_EFFORT", "high"),
            codex_sandbox=os.environ.get("CODEX_SANDBOX", "workspace-write"),
            codex_full_auto=os.environ.get("CODEX_FULL_AUTO", "true").lower() == "true",
            codex_extra_args=os.environ.get("CODEX_EXTRA_ARGS", ""),
        )
