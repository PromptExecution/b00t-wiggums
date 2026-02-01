from __future__ import annotations

import argparse
import sys

__version__ = "0.1.0"


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the Ralph agent loop."""
    from returns.result import Failure

    from ralph.config import RalphConfig
    from ralph.file_manager import initialize_progress_file
    from ralph.runner import run_ralph

    # Initialize progress file if it doesn't exist
    result = initialize_progress_file()
    if isinstance(result, Failure):
        print(f"Error initializing progress file: {result.failure()}", file=sys.stderr)
        return 1

    config = RalphConfig.from_env(tool=args.agent)

    # TODO: Handle --task-id, --dry-run, --verbose flags when implemented
    # For now, just run with max_iterations
    return run_ralph(config, args.max_iterations)


def cmd_status(_args: argparse.Namespace) -> int:
    """Show current task status summary."""
    from returns.result import Failure

    from ralph.config import RalphConfig
    from ralph.taskmaster_adapter import create_client

    config = RalphConfig.from_env()
    client = create_client(
        prefer_mcp=config.use_mcp,
        mcp_url=config.taskmaster_url,
    )

    tasks_result = client.get_all_tasks()
    if isinstance(tasks_result, Failure):
        print(f"❌ Error fetching tasks: {tasks_result.failure()}", file=sys.stderr)
        return 1

    tasks = tasks_result.unwrap()

    # Count tasks by status
    done_count = sum(1 for t in tasks if t.status == "done")
    in_progress_count = sum(1 for t in tasks if t.status == "in-progress")
    pending_count = sum(1 for t in tasks if t.status == "pending")
    blocked_count = sum(1 for t in tasks if t.blocked_by)

    total = len(tasks)

    print("=" * 50)
    print(f"Total Tasks: {total}")
    print(f"Completed: {done_count} | In Progress: {in_progress_count} | Pending: {pending_count} | Blocked: {blocked_count}")
    print("=" * 50)

    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    """List all stories with optional filtering."""
    from returns.result import Failure

    from ralph.config import RalphConfig
    from ralph.taskmaster_adapter import create_client

    config = RalphConfig.from_env()
    client = create_client(
        prefer_mcp=config.use_mcp,
        mcp_url=config.taskmaster_url,
    )

    tasks_result = client.get_all_tasks()
    if isinstance(tasks_result, Failure):
        print(f"❌ Error fetching tasks: {tasks_result.failure()}", file=sys.stderr)
        return 1

    tasks = tasks_result.unwrap()

    # Apply filter if specified
    filter_status = args.filter
    if filter_status != "all":
        tasks = [t for t in tasks if t.status == filter_status]

    # Sort by priority
    tasks.sort(key=lambda t: t.priority)

    print(f"\n{'ID':<15} {'Status':<15} {'Priority':<10} {'Title'}")
    print("=" * 80)

    status_icons = {
        "done": "✓",
        "in-progress": "⚡",
        "pending": "○",
        "review": "👀",
        "cancelled": "✗",
    }

    for task in tasks:
        icon = status_icons.get(task.status, "?")
        blocked_marker = " [BLOCKED]" if task.blocked_by else ""
        print(f"{task.id:<15} {icon} {task.status:<13} {task.priority:<10} {task.title}{blocked_marker}")

    print()
    return 0


def main() -> int:
    """Main entry point for ralph CLI."""
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph - Autonomous coding agent loop runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with amp agent for 10 iterations
  ralph run --agent amp --max-iterations 10

  # Run with OpenCode
  ralph run --agent opencode

  # Show task status summary
  ralph status

  # List all tasks
  ralph list-tasks

  # List only pending tasks
  ralph list-tasks --filter pending
""",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Execute the agent loop",
        description="Run Ralph's autonomous coding loop with specified agent",
    )
    run_parser.add_argument(
        "--agent",
        choices=["amp", "claude", "codex", "opencode"],
        default="amp",
        help="Agent to run (default: amp)",
    )
    run_parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations to run (default: 10)",
    )
    # Future flags for enhanced functionality
    run_parser.add_argument(
        "--task-id",
        type=str,
        help="Run a specific task by ID (not yet implemented)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running (not yet implemented)",
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output (not yet implemented)",
    )
    run_parser.set_defaults(func=cmd_run)

    # 'status' subcommand
    status_parser = subparsers.add_parser(
        "status",
        help="Show current task status summary",
        description="Display a summary of task completion status",
    )
    status_parser.set_defaults(func=cmd_status)

    # 'list-tasks' subcommand
    list_parser = subparsers.add_parser(
        "list-tasks",
        help="List all stories",
        description="List all tasks with optional status filtering",
    )
    list_parser.add_argument(
        "--filter",
        choices=["all", "pending", "in-progress", "done"],
        default="all",
        help="Filter tasks by status (default: all)",
    )
    list_parser.set_defaults(func=cmd_list_tasks)

    args = parser.parse_args()

    # If no subcommand provided, show help
    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
