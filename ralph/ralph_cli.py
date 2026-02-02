from __future__ import annotations

import argparse
import sys

__version__ = "0.1.0"


def main() -> int:
    """Main entry point for ralph CLI."""
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph - Autonomous coding agent loop runner",
    )
    parser.add_argument(
        "--tool",
        choices=["amp", "claude", "codex", "opencode"],
        default="amp",
        help="Tool to run (default: amp)",
    )
    parser.add_argument(
        "max_iterations",
        nargs="?",
        type=int,
        default=10,
        help="Maximum iterations to run (default: 10)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Import here to avoid circular imports
    from returns.result import Failure

    from ralph.config import RalphConfig
    from ralph.file_manager import initialize_progress_file
    from ralph.runner import run_ralph

    # Initialize progress file if it doesn't exist
    result = initialize_progress_file()
    if isinstance(result, Failure):
        print(f"Error initializing progress file: {result.failure()}", file=sys.stderr)
        return 1

    config = RalphConfig.from_env(tool=args.tool)
    return run_ralph(config, args.max_iterations)


if __name__ == "__main__":
    sys.exit(main())
