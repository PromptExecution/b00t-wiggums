"""TaskMaster adapter - abstraction for task management via MCP or CLI.

IMPORTANT: This module NEVER accesses tasks.json directly.
All task operations go through TaskMaster-AI's interface (MCP or CLI).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from returns.maybe import Maybe, Nothing, Some
from returns.result import Failure, Result, Success


@dataclass(frozen=True)
class Task:
    """Represents a single task from TaskMaster."""

    id: str
    title: str
    description: str
    status: str  # pending, in-progress, done, review, cancelled
    priority: int
    acceptance_criteria: list[str]
    depends_on: list[str]
    blocked_by: list[str]  # Auto-computed from dependencies
    notes: list[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create Task from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", 0),
            acceptance_criteria=data.get("acceptanceCriteria", []),
            depends_on=data.get("dependsOn", []),
            blocked_by=data.get("blockedBy", []),
            notes=data.get("notes", []),
            created_at=data.get("createdAt", datetime.now().isoformat()),
            updated_at=data.get("updatedAt", datetime.now().isoformat()),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Task to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "acceptanceCriteria": self.acceptance_criteria,
            "dependsOn": self.depends_on,
            "blockedBy": self.blocked_by,
            "notes": self.notes,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


class TaskMasterClient(Protocol):
    """Protocol for task management operations."""

    def get_next_task(self) -> Result[Task, Exception]:
        """Get the next available task (highest priority, not blocked)."""
        ...

    def get_task_by_id(self, task_id: str) -> Result[Task, Exception]:
        """Get a specific task by ID."""
        ...

    def update_task_status(
        self, task_id: str, status: str
    ) -> Result[None, Exception]:
        """Update task status (pending, in-progress, done, etc.)."""
        ...

    def add_task_note(
        self, task_id: str, note: str
    ) -> Result[None, Exception]:
        """Add a timestamped note to a task."""
        ...

    def get_all_tasks(self) -> Result[list[Task], Exception]:
        """Get all tasks from the task list."""
        ...


@dataclass(frozen=True, slots=True)
class FileTaskMasterClient:
    """File-based TaskMaster client - reads/writes tasks.json directly."""

    tasks_file: Path = Path("tasks.json")

    def get_next_task(self) -> Result[Task, Exception]:
        """Get the next available task from tasks.json."""
        tasks_result = self.get_all_tasks()
        if isinstance(tasks_result, Failure):
            return tasks_result

        tasks = tasks_result.unwrap()

        # Filter for pending tasks that aren't blocked
        available = [
            t for t in tasks
            if t.status == "pending" and not t.blocked_by
        ]

        if not available:
            return Failure(Exception("No available tasks"))

        # Sort by priority (lowest number = highest priority)
        available.sort(key=lambda t: t.priority)

        return Success(available[0])

    def get_task_by_id(self, task_id: str) -> Result[Task, Exception]:
        """Get a specific task by ID from tasks.json."""
        tasks_result = self.get_all_tasks()
        if isinstance(tasks_result, Failure):
            return tasks_result

        tasks = tasks_result.unwrap()
        for task in tasks:
            if task.id == task_id:
                return Success(task)

        return Failure(Exception(f"Task {task_id} not found"))

    def update_task_status(
        self, task_id: str, status: str
    ) -> Result[None, Exception]:
        """Update task status in tasks.json."""
        try:
            # Read current data
            data = json.loads(self.tasks_file.read_text())
            tasks_data = data.get("tasks", [])

            # Find and update task
            found = False
            for task_dict in tasks_data:
                if task_dict.get("id") == task_id:
                    task_dict["status"] = status
                    task_dict["updatedAt"] = datetime.now().isoformat()
                    found = True
                    break

            if not found:
                return Failure(Exception(f"Task {task_id} not found"))

            # Write back
            data["tasks"] = tasks_data
            self.tasks_file.write_text(json.dumps(data, indent=2) + "\n")
            return Success(None)

        except Exception as exc:
            return Failure(exc)

    def add_task_note(
        self, task_id: str, note: str
    ) -> Result[None, Exception]:
        """Add a timestamped note to a task in tasks.json."""
        try:
            # Read current data
            data = json.loads(self.tasks_file.read_text())
            tasks_data = data.get("tasks", [])

            # Find and update task
            found = False
            timestamped_note = f"{datetime.now().isoformat()}: {note}"
            for task_dict in tasks_data:
                if task_dict.get("id") == task_id:
                    notes = task_dict.get("notes", [])
                    notes.append(timestamped_note)
                    task_dict["notes"] = notes
                    task_dict["updatedAt"] = datetime.now().isoformat()
                    found = True
                    break

            if not found:
                return Failure(Exception(f"Task {task_id} not found"))

            # Write back
            data["tasks"] = tasks_data
            self.tasks_file.write_text(json.dumps(data, indent=2) + "\n")
            return Success(None)

        except Exception as exc:
            return Failure(exc)

    def get_all_tasks(self) -> Result[list[Task], Exception]:
        """Get all tasks from tasks.json."""
        try:
            if not self.tasks_file.exists():
                return Failure(Exception(f"Tasks file not found: {self.tasks_file}"))

            data = json.loads(self.tasks_file.read_text())
            tasks_data = data.get("tasks", [])
            tasks = [Task.from_dict(t) for t in tasks_data]
            return Success(tasks)
        except Exception as exc:
            return Failure(exc)


@dataclass(frozen=True, slots=True)
class CLITaskMasterClient:
    """TaskMaster CLI client - uses taskmaster command-line tool.

    Respects separation of concerns: TaskMaster-AI owns task CRUD,
    Ralph consumes via CLI interface.
    """

    def get_next_task(self) -> Result[Task, Exception]:
        """Get the next available task via taskmaster CLI."""
        tasks_result = self.get_all_tasks()
        if isinstance(tasks_result, Failure):
            return tasks_result

        tasks = tasks_result.unwrap()

        # Filter for pending tasks that aren't blocked
        available = [
            t for t in tasks
            if t.status == "pending" and not t.blocked_by
        ]

        if not available:
            return Failure(Exception("No available tasks"))

        # Sort by priority (lowest number = highest priority)
        available.sort(key=lambda t: t.priority)

        return Success(available[0])

    def get_task_by_id(self, task_id: str) -> Result[Task, Exception]:
        """Get a specific task by ID via CLI."""
        try:
            result = subprocess.run(
                ["taskmaster", "get", task_id, "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            task_data = json.loads(result.stdout)
            return Success(Task.from_dict(task_data))
        except subprocess.CalledProcessError as e:
            return Failure(Exception(f"taskmaster get failed: {e.stderr}"))
        except FileNotFoundError:
            return Failure(Exception("taskmaster CLI not found"))
        except Exception as exc:
            return Failure(exc)

    def update_task_status(
        self, task_id: str, status: str
    ) -> Result[None, Exception]:
        """Update task status via CLI."""
        try:
            subprocess.run(
                ["taskmaster", "update", task_id, "--status", status],
                capture_output=True,
                text=True,
                check=True,
            )
            return Success(None)
        except subprocess.CalledProcessError as e:
            return Failure(Exception(f"taskmaster update failed: {e.stderr}"))
        except FileNotFoundError:
            return Failure(Exception("taskmaster CLI not found"))
        except Exception as exc:
            return Failure(exc)

    def add_task_note(
        self, task_id: str, note: str
    ) -> Result[None, Exception]:
        """Add a timestamped note via CLI."""
        try:
            timestamped_note = f"{datetime.now().isoformat()}: {note}"
            subprocess.run(
                ["taskmaster", "add-note", task_id, timestamped_note],
                capture_output=True,
                text=True,
                check=True,
            )
            return Success(None)
        except subprocess.CalledProcessError as e:
            return Failure(Exception(f"taskmaster add-note failed: {e.stderr}"))
        except FileNotFoundError:
            return Failure(Exception("taskmaster CLI not found"))
        except Exception as exc:
            return Failure(exc)

    def get_all_tasks(self) -> Result[list[Task], Exception]:
        """Get all tasks via CLI."""
        try:
            result = subprocess.run(
                ["taskmaster", "list", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            tasks_data = data.get("tasks", [])
            tasks = [Task.from_dict(t) for t in tasks_data]
            return Success(tasks)
        except subprocess.CalledProcessError as e:
            return Failure(Exception(f"taskmaster list failed: {e.stderr}"))
        except FileNotFoundError:
            return Failure(Exception("taskmaster CLI not found - install taskmaster-ai"))
        except Exception as exc:
            return Failure(exc)


@dataclass(frozen=True, slots=True)
class MCPTaskMasterClient:
    """MCP-based TaskMaster client - communicates with TaskMaster MCP server."""

    server_url: str | None = None

    def get_next_task(self) -> Result[Task, Exception]:
        """Get the next available task via MCP."""
        # TODO: Implement MCP client using taskmaster-ai MCP tools
        # For now, raise NotImplementedError
        return Failure(NotImplementedError("MCP client not yet implemented"))

    def get_task_by_id(self, _task_id: str) -> Result[Task, Exception]:
        """Get a specific task by ID via MCP."""
        # TODO: Implement MCP client
        return Failure(NotImplementedError("MCP client not yet implemented"))

    def update_task_status(
        self, _task_id: str, _status: str
    ) -> Result[None, Exception]:
        """Update task status via MCP."""
        # TODO: Implement MCP client
        return Failure(NotImplementedError("MCP client not yet implemented"))

    def add_task_note(
        self, _task_id: str, _note: str
    ) -> Result[None, Exception]:
        """Add a timestamped note via MCP."""
        # TODO: Implement MCP client
        return Failure(NotImplementedError("MCP client not yet implemented"))

    def get_all_tasks(self) -> Result[list[Task], Exception]:
        """Get all tasks via MCP."""
        # TODO: Implement MCP client
        return Failure(NotImplementedError("MCP client not yet implemented"))


def create_client(
    prefer_mcp: bool = False,
    mcp_url: str | None = None,
    tasks_file: Path | None = None,
) -> TaskMasterClient:
    """
    Factory function to create appropriate TaskMaster client.

    Args:
        prefer_mcp: If True, try MCP first and fallback to file-based
        mcp_url: URL for MCP server (optional)
        tasks_file: Path to tasks.json file (default: ./tasks.json)

    Returns:
        TaskMasterClient implementation (MCP, CLI, or file-based)
    """
    if prefer_mcp:
        # Try MCP client first
        mcp_client = MCPTaskMasterClient(server_url=mcp_url)
        # Test if MCP is available by trying to get tasks
        test_result = mcp_client.get_all_tasks()
        if isinstance(test_result, Success):
            return mcp_client

        # MCP failed, fall back to file-based
        return FileTaskMasterClient(tasks_file=tasks_file or Path("tasks.json"))

    # Default to file-based client
    return FileTaskMasterClient(tasks_file=tasks_file or Path("tasks.json"))


def get_current_branch() -> Maybe[str]:
    """Get the configured branch name from TaskMaster CLI."""
    try:
        result = subprocess.run(
            ["taskmaster", "metadata", "--field", "branchName"],
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        if branch:
            return Some(branch)
        return Nothing
    except Exception:
        return Nothing
