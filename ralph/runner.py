from __future__ import annotations

import time
from pathlib import Path

from returns.result import Failure

from ralph.config import RalphConfig
from ralph.executors import create_executor


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_ralph(config: RalphConfig, max_iterations: int) -> int:
    """
    Run Ralph autonomous agent loop.

    Args:
        config: Ralph configuration
        max_iterations: Maximum number of iterations to run

    Returns:
        0 on completion (when <promise>COMPLETE</promise> is detected)
        1 if max iterations reached without completion
    """
    print(f"Starting Ralph - Tool: {config.tool} - Max iterations: {max_iterations}")

    executor = create_executor(config)

    for i in range(1, max_iterations + 1):
        print("")
        print("===============================================================")
        print(f"  Ralph Iteration {i} of {max_iterations} ({config.tool})")
        print("===============================================================")

        result = executor.execute()

        if isinstance(result, Failure):
            print(f"❌ Error executing {config.tool}: {result.failure()}")
            print(f"Iteration {i} failed. Continuing...")
            time.sleep(2)
            continue

        output = result.unwrap()

        # Check for completion signal
        if "<promise>COMPLETE</promise>" in output:
            print("")
            print("Ralph completed all tasks!")
            print(f"Completed at iteration {i} of {max_iterations}")
            return 0

        print(f"Iteration {i} complete. Continuing...")
        time.sleep(2)

    print("")
    print(
        f"Ralph reached max iterations ({max_iterations}) without completing all tasks."
    )
    root = _project_root()
    progress_file = root / "progress.txt"
    print(f"Check {progress_file} for status.")
    return 1
