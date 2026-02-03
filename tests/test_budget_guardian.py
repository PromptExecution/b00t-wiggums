"""Tests for the Officer Clancy Budget Guardian module."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from returns.result import Failure, Success

from ralph.budget_guardian import (
    AttemptResult,
    BudgetConfig,
    BudgetExceededError,
    BudgetGuardian,
    BudgetState,
    EscalationLevel,
    create_guardian_from_env,
)


class TestBudgetConfig:
    """Tests for BudgetConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BudgetConfig()
        assert config.max_attempts == 10
        assert config.budget_limit == 100.0
        assert config.cost_per_attempt == 10.0
        assert config.warning_threshold == 0.5
        assert config.critical_threshold == 0.8
        assert config.exceeded_threshold == 0.9
        assert config.allow_budget_overflow is False

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BudgetConfig(
            max_attempts=5,
            budget_limit=50.0,
            cost_per_attempt=5.0,
            warning_threshold=0.4,
            critical_threshold=0.7,
            exceeded_threshold=0.85,
            allow_budget_overflow=True,
        )
        assert config.max_attempts == 5
        assert config.budget_limit == 50.0
        assert config.cost_per_attempt == 5.0
        assert config.warning_threshold == 0.4
        assert config.critical_threshold == 0.7
        assert config.exceeded_threshold == 0.85
        assert config.allow_budget_overflow is True


class TestBudgetState:
    """Tests for BudgetState dataclass."""

    def test_default_state(self) -> None:
        """Test default state initialization."""
        state = BudgetState()
        assert state.total_attempts == 0
        assert state.total_cost == 0.0
        assert state.successful_attempts == 0
        assert state.failed_attempts == 0
        assert state.escalation_level == EscalationLevel.NORMAL
        assert state.notes == []
        assert state.last_attempt_time is None
        assert isinstance(state.start_time, datetime)


class TestBudgetGuardian:
    """Tests for BudgetGuardian class."""

    def test_initial_state(self) -> None:
        """Test guardian initial state."""
        config = BudgetConfig()
        guardian = BudgetGuardian(config)

        assert guardian.remaining_attempts == 10
        assert guardian.remaining_budget == 100.0
        assert guardian.budget_percentage_used == 0.0
        assert guardian.state.escalation_level == EscalationLevel.NORMAL

    def test_authorize_attempt_success(self) -> None:
        """Test successful attempt authorization."""
        config = BudgetConfig(max_attempts=5, budget_limit=50.0, cost_per_attempt=10.0)
        guardian = BudgetGuardian(config)

        result = guardian.authorize_attempt()

        assert isinstance(result, Success)
        attempt = result.unwrap()
        assert isinstance(attempt, AttemptResult)
        assert attempt.attempt_number == 1
        assert attempt.cost == 10.0
        assert attempt.remaining_budget == 40.0
        assert attempt.remaining_attempts == 4

    def test_authorize_attempt_custom_cost(self) -> None:
        """Test attempt authorization with custom cost."""
        config = BudgetConfig(max_attempts=10, budget_limit=100.0)
        guardian = BudgetGuardian(config)

        result = guardian.authorize_attempt(task_cost=25.0)

        assert isinstance(result, Success)
        attempt = result.unwrap()
        assert attempt.cost == 25.0
        assert attempt.remaining_budget == 75.0

    def test_authorize_attempt_max_attempts_exceeded(self) -> None:
        """Test denial when max attempts exceeded."""
        config = BudgetConfig(max_attempts=2, budget_limit=100.0, cost_per_attempt=10.0)
        guardian = BudgetGuardian(config)

        # Use up all attempts
        guardian.authorize_attempt()
        guardian.authorize_attempt()

        # Third attempt should fail
        result = guardian.authorize_attempt()

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, BudgetExceededError)
        assert "MAXIMUM ATTEMPTS REACHED" in str(error)

    def test_authorize_attempt_insufficient_budget(self) -> None:
        """Test denial when budget insufficient."""
        config = BudgetConfig(max_attempts=10, budget_limit=25.0, cost_per_attempt=10.0)
        guardian = BudgetGuardian(config)

        # Use up most of budget
        guardian.authorize_attempt()  # 15 remaining
        guardian.authorize_attempt()  # 5 remaining

        # Third attempt should fail (needs 10, has 5)
        result = guardian.authorize_attempt()

        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, BudgetExceededError)
        assert "INSUFFICIENT BUDGET" in str(error)

    def test_allow_budget_overflow(self) -> None:
        """Test that overflow is allowed when configured."""
        config = BudgetConfig(
            max_attempts=10,
            budget_limit=25.0,
            cost_per_attempt=10.0,
            allow_budget_overflow=True,
        )
        guardian = BudgetGuardian(config)

        # Use up budget
        guardian.authorize_attempt()  # 15 remaining
        guardian.authorize_attempt()  # 5 remaining

        # Third attempt should succeed with overflow
        result = guardian.authorize_attempt()

        assert isinstance(result, Success)
        # Budget is now negative, but allowed
        assert guardian.remaining_budget == 0.0  # max(0, -5) = 0

    def test_record_success(self) -> None:
        """Test recording successful attempts."""
        config = BudgetConfig()
        guardian = BudgetGuardian(config)

        guardian.authorize_attempt()
        guardian.record_success()

        assert guardian.state.successful_attempts == 1
        assert guardian.state.failed_attempts == 0

    def test_record_failure(self) -> None:
        """Test recording failed attempts."""
        config = BudgetConfig()
        guardian = BudgetGuardian(config)

        guardian.authorize_attempt()
        guardian.record_failure("Test failure reason")

        assert guardian.state.successful_attempts == 0
        assert guardian.state.failed_attempts == 1
        assert "Test failure reason" in guardian.state.notes[-1]

    def test_escalation_levels(self) -> None:
        """Test escalation level progression."""
        config = BudgetConfig(
            max_attempts=10,
            budget_limit=100.0,
            cost_per_attempt=10.0,
            warning_threshold=0.5,
            critical_threshold=0.8,
            exceeded_threshold=0.9,
        )
        guardian = BudgetGuardian(config)

        # Start at NORMAL
        assert guardian.state.escalation_level == EscalationLevel.NORMAL

        # After 5 attempts (50%), should be WARNING
        for _ in range(5):
            guardian.authorize_attempt()
        assert guardian.state.escalation_level == EscalationLevel.WARNING

        # After 8 attempts (80%), should be CRITICAL
        for _ in range(3):
            guardian.authorize_attempt()
        assert guardian.state.escalation_level == EscalationLevel.CRITICAL

        # After 9 attempts (90%), should be EXCEEDED
        guardian.authorize_attempt()
        assert guardian.state.escalation_level == EscalationLevel.EXCEEDED

    def test_escalation_callback(self) -> None:
        """Test escalation callback is invoked on level change."""
        callback = MagicMock()
        config = BudgetConfig(
            max_attempts=10,
            budget_limit=100.0,
            cost_per_attempt=10.0,
            warning_threshold=0.5,
        )
        guardian = BudgetGuardian(config, escalation_callback=callback)

        # Should not trigger callback yet
        for _ in range(4):
            guardian.authorize_attempt()
        callback.assert_not_called()

        # 5th attempt should trigger WARNING
        guardian.authorize_attempt()
        callback.assert_called_once()
        call_args = callback.call_args
        assert call_args[0][0] == EscalationLevel.WARNING

    def test_get_elapsed_time(self) -> None:
        """Test elapsed time calculation."""
        config = BudgetConfig()
        guardian = BudgetGuardian(config)

        # Should be very small on creation
        elapsed = guardian.get_elapsed_time()
        assert elapsed >= 0
        assert elapsed < 1.0  # Less than 1 second

    def test_get_summary(self) -> None:
        """Test summary generation."""
        config = BudgetConfig(max_attempts=5, budget_limit=50.0, cost_per_attempt=10.0)
        guardian = BudgetGuardian(config)

        guardian.authorize_attempt()
        guardian.record_success()
        guardian.authorize_attempt()
        guardian.record_failure()

        summary = guardian.get_summary()

        assert "Officer Clancy Budget Report" in summary
        assert "Attempts: 2/5" in summary
        assert "✓1 ✗1" in summary
        assert "Budget: 20.00/50.00" in summary
        assert "40.0% used" in summary

    def test_reset(self) -> None:
        """Test guardian reset."""
        config = BudgetConfig(max_attempts=5, budget_limit=50.0, cost_per_attempt=10.0)
        guardian = BudgetGuardian(config)

        # Make some attempts
        guardian.authorize_attempt()
        guardian.authorize_attempt()
        guardian.record_success()

        # Verify state changed
        assert guardian.state.total_attempts == 2
        assert guardian.state.total_cost == 20.0

        # Reset
        guardian.reset()

        # Verify state is fresh
        assert guardian.state.total_attempts == 0
        assert guardian.state.total_cost == 0.0
        assert guardian.remaining_attempts == 5
        assert guardian.remaining_budget == 50.0

    def test_budget_percentage_with_zero_limit(self) -> None:
        """Test budget percentage when limit is zero."""
        config = BudgetConfig(budget_limit=0.0)
        guardian = BudgetGuardian(config)

        assert guardian.budget_percentage_used == 1.0


class TestBudgetExceededError:
    """Tests for BudgetExceededError exception."""

    def test_error_message(self) -> None:
        """Test error message."""
        error = BudgetExceededError("Test message")
        assert str(error) == "Test message"

    def test_error_with_budget_data(self) -> None:
        """Test error with budget data attached."""
        state = BudgetState(total_attempts=5, total_cost=50.0)
        error = BudgetExceededError("Budget exceeded", budget_data=state)

        assert error.budget_data is not None
        assert error.budget_data.total_attempts == 5
        assert error.budget_data.total_cost == 50.0


class TestCreateGuardianFromEnv:
    """Tests for create_guardian_from_env helper."""

    def test_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with default environment."""
        # Clear any existing env vars
        monkeypatch.delenv("RALPH_MAX_ATTEMPTS", raising=False)
        monkeypatch.delenv("RALPH_BUDGET_LIMIT", raising=False)
        monkeypatch.delenv("RALPH_COST_PER_ATTEMPT", raising=False)

        guardian = create_guardian_from_env()

        assert guardian.config.max_attempts == 10
        assert guardian.config.budget_limit == 100.0
        assert guardian.config.cost_per_attempt == 10.0

    def test_with_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with custom environment variables."""
        monkeypatch.setenv("RALPH_MAX_ATTEMPTS", "5")
        monkeypatch.setenv("RALPH_BUDGET_LIMIT", "50.0")
        monkeypatch.setenv("RALPH_COST_PER_ATTEMPT", "5.0")

        guardian = create_guardian_from_env()

        assert guardian.config.max_attempts == 5
        assert guardian.config.budget_limit == 50.0
        assert guardian.config.cost_per_attempt == 5.0

    def test_with_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with explicit overrides (should take precedence)."""
        monkeypatch.setenv("RALPH_MAX_ATTEMPTS", "100")

        guardian = create_guardian_from_env(max_attempts=3)

        assert guardian.config.max_attempts == 3  # Override wins


class TestEscalationLevel:
    """Tests for EscalationLevel enum."""

    def test_values(self) -> None:
        """Test enum values."""
        assert EscalationLevel.NORMAL.value == "normal"
        assert EscalationLevel.WARNING.value == "warning"
        assert EscalationLevel.CRITICAL.value == "critical"
        assert EscalationLevel.EXCEEDED.value == "exceeded"


class TestAttemptResult:
    """Tests for AttemptResult dataclass."""

    def test_creation(self) -> None:
        """Test AttemptResult creation."""
        result = AttemptResult(
            attempt_number=1,
            cost=10.0,
            remaining_budget=90.0,
            remaining_attempts=9,
            escalation_level=EscalationLevel.NORMAL,
        )

        assert result.attempt_number == 1
        assert result.cost == 10.0
        assert result.remaining_budget == 90.0
        assert result.remaining_attempts == 9
        assert result.escalation_level == EscalationLevel.NORMAL
