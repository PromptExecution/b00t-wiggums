---
name: officer-clancy
description: "Officer Clancy Budget Guardian - Real-time budget and attempt limit enforcement for AI agents. Use when you need to prevent runaway AI loops, track resource consumption, or implement cost controls. Triggers on: budget limit, cost tracking, prevent runaway, max attempts, resource management, agent guardrails."
user-invocable: true
---

# Officer Clancy: The Budget Guardian

Officer Clancy is the responsible adult supervising enthusiastic (but potentially costly) AI agents. Unlike Ralph Wiggum's unbounded determination, Officer Clancy embodies strategic resource management.

---

## The Job

Protect your AI agent workflows from runaway costs by:
- **Tracking attempts**: Monitor how many times a task has been attempted
- **Managing budgets**: Set and enforce computational/time budgets
- **Escalating alerts**: Provide intelligent warnings at configurable thresholds
- **Preventing infinite loops**: Stop execution when limits are exceeded

---

## Quick Start

### Basic Usage

```python
from ralph.budget_guardian import BudgetConfig, BudgetGuardian

# Configure limits
config = BudgetConfig(
    max_attempts=10,       # Maximum task attempts
    budget_limit=100.0,    # Abstract budget units
    cost_per_attempt=10.0, # Cost deducted per attempt
)

# Create guardian
guardian = BudgetGuardian(config)

# Before each iteration
result = guardian.authorize_attempt()
if result.is_failure():
    print(f"Denied: {result.failure()}")
else:
    attempt = result.unwrap()
    print(f"Attempt {attempt.attempt_number} authorized")
    
    # ... execute the actual work ...
    
    guardian.record_success()  # or record_failure()
```

### With Ralph Runner

Officer Clancy is integrated into Ralph's iteration loop but **disabled by default** (opt-in). Configure via environment variables:

```bash
# Enable budget guardian (disabled by default for opt-in behavior)
export RALPH_BUDGET_ENABLED=true

# Set limits
export RALPH_MAX_ATTEMPTS=10
export RALPH_BUDGET_LIMIT=100.0
export RALPH_COST_PER_ATTEMPT=10.0

# Allow going over budget with warning (not recommended)
export RALPH_BUDGET_ALLOW_OVERFLOW=false
```

Or pass configuration directly:

```bash
uv run ralph run --tool amp --max-iterations 10
```

---

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_attempts` | 10 | Maximum number of task attempts |
| `budget_limit` | 100.0 | Total budget limit (abstract units) |
| `cost_per_attempt` | 10.0 | Cost deducted per attempt |
| `warning_threshold` | 0.5 | Percentage for warning alerts (50%) |
| `critical_threshold` | 0.8 | Percentage for critical alerts (80%) |
| `exceeded_threshold` | 0.9 | Percentage at which to deny attempts (90%) |
| `allow_budget_overflow` | False | Allow continuing past budget with warning |

---

## Escalation Levels

Officer Clancy uses four escalation levels:

| Level | Trigger | Behavior |
|-------|---------|----------|
| 🟢 NORMAL | < 50% used | Proceed normally |
| 🟡 WARNING | 50-80% used | Log warning, continue |
| 🟠 CRITICAL | 80-90% used | Log critical alert, continue |
| 🔴 EXCEEDED | > 90% or limit hit | Deny attempt, stop execution |

### Escalation Callback

Register a callback to react to escalation changes:

```python
def my_callback(level, state):
    if level == EscalationLevel.CRITICAL:
        send_slack_alert(f"Budget critical: {state.total_cost}/{config.budget_limit}")

guardian = BudgetGuardian(config, escalation_callback=my_callback)
```

---

## AttemptResult

When an attempt is authorized, you receive an `AttemptResult`:

```python
@dataclass
class AttemptResult:
    attempt_number: int        # Sequential attempt number
    cost: float               # Cost of this attempt
    remaining_budget: float   # Budget remaining after this attempt
    remaining_attempts: int   # Attempts remaining after this one
    escalation_level: str     # Current escalation level
```

---

## Budget Summary Report

Get a human-readable summary at any time:

```python
print(guardian.get_summary())
```

Output:
```
==================================================
🚨 Officer Clancy Budget Report
==================================================
📊 Attempts: 5/10 (✓4 ✗1)
💰 Budget: 50.00/100.00 (50.0% used)
⏱️  Elapsed: 123.4s
🚦 Status: WARNING
==================================================
```

---

## Integration with AgentGuard

Officer Clancy is inspired by [AgentGuard](https://github.com/dipampaul17/AgentGuard), a real-time guardrail that tracks token spend and kills runaway LLM/agent loops.

Key differences:
- **AgentGuard**: JavaScript/Node.js, tracks actual API costs in USD, intercepts HTTP calls
- **Officer Clancy**: Python, tracks abstract budget units, integrates with Ralph's iteration loop

You can use both together:
- AgentGuard for real-time USD cost tracking at the API level
- Officer Clancy for attempt-based iteration control at the workflow level

---

## Design Principles

### Budget, Not Brutality

Officer Clancy isn't about shutting down creativity. It's about channeling AI persistence into productive, efficient problem-solving. Sometimes, the most intelligent action is knowing when to pause and recalibrate.

### Governance Challenge

AI agents need boundaries. While Ralph Wiggum represents unbridled determination, Officer Clancy embodies strategic resource management. It's not just about stopping an agent; it's about guiding it intelligently.

### Cost-Efficiency Optimization

By preventing infinite loops and resource drain, Officer Clancy helps you:
- Avoid surprise cloud bills
- Detect stuck or failing tasks early
- Make data-driven decisions about task complexity
- Maintain predictable operational costs

---

## Example: Full Workflow

```python
from ralph.budget_guardian import BudgetConfig, BudgetGuardian, EscalationLevel

def run_ai_workflow():
    # Configure for 5 attempts with 50 unit budget
    config = BudgetConfig(
        max_attempts=5,
        budget_limit=50.0,
        cost_per_attempt=10.0,
    )
    
    # Create guardian with escalation callback
    def on_escalation(level, state):
        if level == EscalationLevel.WARNING:
            print(f"⚠️ Warning: {state.budget_percentage_used:.0%} budget used")
        elif level == EscalationLevel.CRITICAL:
            print(f"🚨 Critical: Consider simplifying the task")
    
    guardian = BudgetGuardian(config, escalation_callback=on_escalation)
    
    for i in range(10):  # Try up to 10 times
        # Request authorization
        result = guardian.authorize_attempt()
        
        if result.is_failure():
            print(f"❌ Stopped: {result.failure()}")
            break
        
        attempt = result.unwrap()
        print(f"🔄 Attempt {attempt.attempt_number}...")
        
        # Simulate work
        success = do_ai_task()
        
        if success:
            guardian.record_success()
            print("✅ Task completed!")
            break
        else:
            guardian.record_failure("AI model returned error")
    
    # Print final report
    print(guardian.get_summary())
```

---

## Melvin's Lucky Hint

🤓 "Always budget your AI's enthusiasm! A well-bounded agent is a productive agent."

---

## See Also

- [Ralph Runner](../ralph/README.md) - Autonomous AI agent loop
- [TaskMaster Integration](../README-MCP.md) - Task management
- [AgentGuard](https://github.com/dipampaul17/AgentGuard) - Real-time cost tracking
