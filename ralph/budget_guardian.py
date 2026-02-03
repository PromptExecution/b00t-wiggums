"""Officer Clancy Budget Guardian - Resource management for AI agents.

This module implements the Officer Clancy protocol for AI agent budget
and attempt management. It prevents runaway agents by:
- Tracking and limiting the number of task attempts
- Managing computational and time budgets
- Providing escalation protocols and intelligent fallback mechanisms
- Preventing infinite loops and resource drain
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from collections.abc import Callable


class BudgetExceededError(RuntimeError):
    """Raised when budget or attempt limits are exceeded."""

    def __init__(self, message: str, budget_data: BudgetState | None = None) -> None:
        super().__init__(message)
        self.budget_data = budget_data


class EscalationLevel(Enum):
    """Escalation levels for budget warnings."""

    NORMAL = "normal"       # Under 50% budget used
    WARNING = "warning"     # 50-80% budget used
    CRITICAL = "critical"   # 80-90% budget used
    EXCEEDED = "exceeded"   # Over 90% or limit hit


@dataclass(frozen=True)
class BudgetConfig:
    """Configuration for budget guardian limits.

    Attributes:
        max_attempts: Maximum number of task attempts before failure (default: 10)
        budget_limit: Total budget limit in abstract units (default: 100.0)
        cost_per_attempt: Cost deducted per attempt (default: 10.0)
        warning_threshold: Percentage at which to issue warnings (default: 0.5)
        critical_threshold: Percentage at which to issue critical alerts (default: 0.8)
        exceeded_threshold: Percentage at which to stop execution (default: 0.9)
        allow_budget_overflow: If True, allows going over budget with warning (default: False)
        escalation_callback: Optional callback for escalation events
    """

    max_attempts: int = 10
    budget_limit: float = 100.0
    cost_per_attempt: float = 10.0
    warning_threshold: float = 0.5
    critical_threshold: float = 0.8
    exceeded_threshold: float = 0.9
    allow_budget_overflow: bool = False


@dataclass
class BudgetState:
    """Current state of budget tracking.

    Mutable dataclass to track real-time budget consumption.
    """

    total_attempts: int = 0
    total_cost: float = 0.0
    successful_attempts: int = 0
    failed_attempts: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    last_attempt_time: datetime | None = None
    escalation_level: EscalationLevel = EscalationLevel.NORMAL
    notes: list[str] = field(default_factory=list)


@dataclass
class AttemptResult:
    """Result of a single authorized attempt.

    Attributes:
        attempt_number: The sequential attempt number
        cost: Cost of this attempt
        remaining_budget: Budget remaining after this attempt
        remaining_attempts: Attempts remaining after this one
        escalation_level: Current escalation level after this attempt
    """

    attempt_number: int
    cost: float
    remaining_budget: float
    remaining_attempts: int
    escalation_level: EscalationLevel


class BudgetGuardian:
    """Officer Clancy - Budget guardian for AI agent resource management.

    Monitors and limits the number of task attempts, manages resource budgets,
    and provides escalation protocols. Think of it as a responsible adult
    supervising an enthusiastic (but potentially costly) AI agent.

    Example:
        >>> config = BudgetConfig(max_attempts=5, budget_limit=50.0, cost_per_attempt=10.0)
        >>> guardian = BudgetGuardian(config)
        >>> # Authorize an attempt
        >>> result = guardian.authorize_attempt()
        >>> if isinstance(result, Success):
        ...     attempt = result.unwrap()
        ...     print(f"Attempt {attempt.attempt_number} authorized")
        ...     # Execute the actual work here
        ...     guardian.record_success()
        ... else:
        ...     print(f"Denied: {result.failure()}")
    """

    def __init__(
        self,
        config: BudgetConfig,
        escalation_callback: Callable[[EscalationLevel, BudgetState], None] | None = None,
    ) -> None:
        """Initialize the budget guardian.

        Args:
            config: Budget configuration with limits and thresholds
            escalation_callback: Optional callback invoked on escalation changes
        """
        self._config = config
        self._state = BudgetState()
        self._escalation_callback = escalation_callback

    @property
    def config(self) -> BudgetConfig:
        """Get the budget configuration."""
        return self._config

    @property
    def state(self) -> BudgetState:
        """Get the current budget state."""
        return self._state

    @property
    def remaining_attempts(self) -> int:
        """Get the number of remaining attempts."""
        return max(0, self._config.max_attempts - self._state.total_attempts)

    @property
    def remaining_budget(self) -> float:
        """Get the remaining budget."""
        return max(0.0, self._config.budget_limit - self._state.total_cost)

    @property
    def budget_percentage_used(self) -> float:
        """Get the percentage of budget used (0.0 to 1.0+)."""
        if self._config.budget_limit <= 0:
            return 1.0
        return self._state.total_cost / self._config.budget_limit

    def _update_escalation_level(self) -> EscalationLevel:
        """Update and return the current escalation level based on budget usage."""
        percentage = self.budget_percentage_used
        attempt_percentage = (
            self._state.total_attempts / self._config.max_attempts
            if self._config.max_attempts > 0
            else 1.0
        )

        # Use the higher of budget or attempt percentage
        effective_percentage = max(percentage, attempt_percentage)

        if effective_percentage >= self._config.exceeded_threshold:
            new_level = EscalationLevel.EXCEEDED
        elif effective_percentage >= self._config.critical_threshold:
            new_level = EscalationLevel.CRITICAL
        elif effective_percentage >= self._config.warning_threshold:
            new_level = EscalationLevel.WARNING
        else:
            new_level = EscalationLevel.NORMAL

        # Check if escalation level changed
        if new_level != self._state.escalation_level:
            old_level = self._state.escalation_level
            self._state.escalation_level = new_level
            self._state.notes.append(
                f"Escalation: {old_level.value} -> {new_level.value} "
                f"({effective_percentage:.1%} used)"
            )
            if self._escalation_callback:
                self._escalation_callback(new_level, self._state)

        return new_level

    def authorize_attempt(
        self,
        task_cost: float | None = None,
    ) -> Result[AttemptResult, BudgetExceededError]:
        """Authorize a task attempt, deducting from budget.

        Args:
            task_cost: Optional custom cost for this attempt.
                      Defaults to config.cost_per_attempt.

        Returns:
            Success[AttemptResult] if attempt is authorized
            Failure[BudgetExceededError] if limits exceeded
        """
        cost = task_cost if task_cost is not None else self._config.cost_per_attempt

        # Check attempt limit
        if self._state.total_attempts >= self._config.max_attempts:
            error = BudgetExceededError(
                f"MAXIMUM ATTEMPTS REACHED ({self._config.max_attempts})",
                budget_data=self._state,
            )
            self._state.notes.append(f"Denied: max attempts ({self._config.max_attempts})")
            return Failure(error)

        # Check budget limit
        if not self._config.allow_budget_overflow and self.remaining_budget < cost:
            error = BudgetExceededError(
                f"INSUFFICIENT BUDGET (remaining: {self.remaining_budget:.2f}, "
                f"required: {cost:.2f})",
                budget_data=self._state,
            )
            self._state.notes.append(
                f"Denied: insufficient budget "
                f"({self.remaining_budget:.2f} < {cost:.2f})"
            )
            return Failure(error)

        # Authorize the attempt
        self._state.total_attempts += 1
        self._state.total_cost += cost
        self._state.last_attempt_time = datetime.now()

        # Update escalation level
        escalation = self._update_escalation_level()

        result = AttemptResult(
            attempt_number=self._state.total_attempts,
            cost=cost,
            remaining_budget=self.remaining_budget,
            remaining_attempts=self.remaining_attempts,
            escalation_level=escalation,
        )

        self._state.notes.append(
            f"Attempt {result.attempt_number} authorized "
            f"(cost: {cost:.2f}, remaining: {result.remaining_budget:.2f})"
        )

        return Success(result)

    def record_success(self) -> None:
        """Record a successful attempt."""
        self._state.successful_attempts += 1
        self._state.notes.append(
            f"Attempt {self._state.total_attempts} succeeded"
        )

    def record_failure(self, reason: str = "") -> None:
        """Record a failed attempt.

        Args:
            reason: Optional reason for failure
        """
        self._state.failed_attempts += 1
        msg = f"Attempt {self._state.total_attempts} failed"
        if reason:
            msg += f": {reason}"
        self._state.notes.append(msg)

    def get_elapsed_time(self) -> float:
        """Get elapsed time since guardian was created in seconds."""
        return (datetime.now() - self._state.start_time).total_seconds()

    def get_summary(self) -> str:
        """Get a human-readable summary of the budget state."""
        elapsed = self.get_elapsed_time()
        lines = [
            "=" * 50,
            "🚨 Officer Clancy Budget Report",
            "=" * 50,
            f"📊 Attempts: {self._state.total_attempts}/{self._config.max_attempts} "
            f"(✓{self._state.successful_attempts} ✗{self._state.failed_attempts})",
            f"💰 Budget: {self._state.total_cost:.2f}/{self._config.budget_limit:.2f} "
            f"({self.budget_percentage_used:.1%} used)",
            f"⏱️  Elapsed: {elapsed:.1f}s",
            f"🚦 Status: {self._state.escalation_level.value.upper()}",
            "=" * 50,
        ]
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset the budget guardian state for a new session."""
        self._state = BudgetState()


def create_guardian_from_env(
    max_attempts: int | None = None,
    budget_limit: float | None = None,
    cost_per_attempt: float | None = None,
) -> BudgetGuardian:
    """Create a budget guardian with optional overrides.

    Args:
        max_attempts: Override max attempts (default: 10)
        budget_limit: Override budget limit (default: 100.0)
        cost_per_attempt: Override cost per attempt (default: 10.0)

    Returns:
        Configured BudgetGuardian instance
    """
    import os

    config = BudgetConfig(
        max_attempts=max_attempts or int(os.environ.get("RALPH_MAX_ATTEMPTS", "10")),
        budget_limit=budget_limit or float(os.environ.get("RALPH_BUDGET_LIMIT", "100.0")),
        cost_per_attempt=cost_per_attempt
        or float(os.environ.get("RALPH_COST_PER_ATTEMPT", "10.0")),
    )
    return BudgetGuardian(config)


__all__ = [
    "AttemptResult",
    "BudgetConfig",
    "BudgetExceededError",
    "BudgetGuardian",
    "BudgetState",
    "EscalationLevel",
    "create_guardian_from_env",
]
