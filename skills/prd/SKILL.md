---
name: prd
description: "Generate TaskMaster tasks.json for a new feature. Use when planning a feature, starting a new project, or when asked to create tasks. Triggers on: create tasks, write prd for, plan this feature, requirements for, spec out, generate tasks.json."
user-invocable: true
---

# TaskMaster Tasks Generator

Create detailed task lists in TaskMaster JSON format that are clear, actionable, and suitable for autonomous Ralph execution.

---

## The Job

1. Receive a feature description from the user
2. Ask 3-5 essential clarifying questions (with lettered options)
3. Generate structured tasks in TaskMaster format based on answers
4. Save to `.taskmaster/tasks/tasks.json`
5. Optionally save a markdown PRD to `tasks/prd-[feature-name].md` for documentation

**Important:** Do NOT start implementing. Just create the tasks.json file.

---

## Step 1: Clarifying Questions

Ask only critical questions where the initial prompt is ambiguous. Focus on:

- **Problem/Goal:** What problem does this solve?
- **Core Functionality:** What are the key actions?
- **Scope/Boundaries:** What should it NOT do?
- **Success Criteria:** How do we know it's done?

### Format Questions Like This:

```
1. What is the primary goal of this feature?
   A. Improve user onboarding experience
   B. Increase user retention
   C. Reduce support burden
   D. Other: [please specify]

2. Who is the target user?
   A. New users only
   B. Existing users only
   C. All users
   D. Admin users only

3. What is the scope?
   A. Minimal viable version
   B. Full-featured implementation
   C. Just the backend/API
   D. Just the UI
```

This lets users respond with "1A, 2C, 3B" for quick iteration.

---

## Step 2: TaskMaster JSON Output

After gathering answers, generate `.taskmaster/tasks/tasks.json` with this structure:

```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "[Short imperative title]",
      "description": "As a [user], I want [feature] so that [benefit].\n\n[Implementation details and context]",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": [
        "Specific verifiable criterion",
        "Another criterion",
        "Typecheck passes"
      ],
      "dependsOn": [],
      "blockedBy": [],
      "subtasks": [],
      "notes": [],
      "createdAt": "[ISO 8601 timestamp]",
      "updatedAt": "[ISO 8601 timestamp]"
    }
  ],
  "metadata": {
    "project": "[Project Name]",
    "branchName": "ralph/[feature-name-kebab-case]",
    "description": "[Feature description]",
    "taskMasterVersion": "1.0"
  }
}
```

### Task Size Rule
Each task MUST be completable in one Ralph iteration (one context window). If you cannot describe the task in 2-3 sentences, split it into smaller tasks.

### Dependency Tracking
- **dependsOn**: Array of task IDs that this task logically builds on (for documentation)
- **blockedBy**: Array of task IDs that MUST complete before this one can start (enforced by Ralph)

---

## Step 3: Optional Markdown PRD

Generate the PRD with these sections:

### 1. Introduction/Overview
Brief description of the feature and the problem it solves.

### 2. Goals
Specific, measurable objectives (bullet list).

### 3. User Stories
Each story needs:
- **Title:** Short descriptive name
- **Description:** "As a [user], I want [feature] so that [benefit]"
- **Acceptance Criteria:** Verifiable checklist of what "done" means

Each story should be small enough to implement in one focused session.

**Format:**
```markdown
### US-001: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Specific verifiable criterion
- [ ] Another criterion
- [ ] Typecheck/lint passes
- [ ] **[UI stories only]** Verify in browser using dev-browser skill
```

**Important:** 
- Acceptance criteria must be verifiable, not vague. "Works correctly" is bad. "Button shows confirmation dialog before deleting" is good.
- **For any story with UI changes:** Always include "Verify in browser using dev-browser skill" as acceptance criteria. This ensures visual verification of frontend work.

### 4. Functional Requirements
Numbered list of specific functionalities:
- "FR-1: The system must allow users to..."
- "FR-2: When a user clicks X, the system must..."

Be explicit and unambiguous.

### 5. Non-Goals (Out of Scope)
What this feature will NOT include. Critical for managing scope.

### 6. Design Considerations (Optional)
- UI/UX requirements
- Link to mockups if available
- Relevant existing components to reuse

### 7. Technical Considerations (Optional)
- Known constraints or dependencies
- Integration points with existing systems
- Performance requirements

### 8. Success Metrics
How will success be measured?
- "Reduce time to complete X by 50%"
- "Increase conversion rate by 10%"

### 9. Open Questions
Remaining questions or areas needing clarification.

---

## Writing for Junior Developers

The PRD reader may be a junior developer or AI agent. Therefore:

- Be explicit and unambiguous
- Avoid jargon or explain it
- Provide enough detail to understand purpose and core logic
- Number requirements for easy reference
- Use concrete examples where helpful

---

## Output Files

### Required:
- **tasks.json**: `.taskmaster/tasks/tasks.json` (TaskMaster format)

### Optional (for documentation):
- **PRD markdown**: `tasks/prd-[feature-name].md` (human-readable)

---

## Example Output

### tasks.json (Required)

```markdown
# PRD: Task Priority System

## Introduction

Add priority levels to tasks so users can focus on what matters most. Tasks can be marked as high, medium, or low priority, with visual indicators and filtering to help users manage their workload effectively.

## Goals

- Allow assigning priority (high/medium/low) to any task
- Provide clear visual differentiation between priority levels
- Enable filtering and sorting by priority
- Default new tasks to medium priority

## User Stories

### US-001: Add priority field to database
**Description:** As a developer, I need to store task priority so it persists across sessions.

**Acceptance Criteria:**
- [ ] Add priority column to tasks table: 'high' | 'medium' | 'low' (default 'medium')
- [ ] Generate and run migration successfully
- [ ] Typecheck passes

### US-002: Display priority indicator on task cards
**Description:** As a user, I want to see task priority at a glance so I know what needs attention first.

**Acceptance Criteria:**
- [ ] Each task card shows colored priority badge (red=high, yellow=medium, gray=low)
- [ ] Priority visible without hovering or clicking
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-003: Add priority selector to task edit
**Description:** As a user, I want to change a task's priority when editing it.

**Acceptance Criteria:**
- [ ] Priority dropdown in task edit modal
- [ ] Shows current priority as selected
- [ ] Saves immediately on selection change
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

### US-004: Filter tasks by priority
**Description:** As a user, I want to filter the task list to see only high-priority items when I'm focused.

**Acceptance Criteria:**
- [ ] Filter dropdown with options: All | High | Medium | Low
- [ ] Filter persists in URL params
- [ ] Empty state message when no tasks match filter
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: Add `priority` field to tasks table ('high' | 'medium' | 'low', default 'medium')
- FR-2: Display colored priority badge on each task card
- FR-3: Include priority selector in task edit modal
- FR-4: Add priority filter dropdown to task list header
- FR-5: Sort by priority within each status column (high to medium to low)

## Non-Goals

- No priority-based notifications or reminders
- No automatic priority assignment based on due date
- No priority inheritance for subtasks

## Technical Considerations

- Reuse existing badge component with color variants
- Filter state managed via URL search params
- Priority stored in database, not computed

## Success Metrics

- Users can change priority in under 2 clicks
- High-priority tasks immediately visible at top of lists
- No regression in task list performance

## Open Questions

- Should priority affect task ordering within a column?
- Should we add keyboard shortcuts for priority changes?
```

---

### prd-task-priority.md (Optional Documentation)

```markdown
# PRD: Task Priority System

[... Keep existing PRD example for reference ...]
```

---

## Checklist

Before saving tasks.json:

- [ ] Asked clarifying questions with lettered options
- [ ] Incorporated user's answers
- [ ] Each task is small enough (completable in one iteration)
- [ ] Tasks ordered by dependency (schema → backend → UI)
- [ ] Priority numbers match dependency order
- [ ] Every task has verifiable acceptance criteria
- [ ] Every task has "Typecheck passes" as final criterion
- [ ] UI tasks have "Verify in browser using dev-browser skill"
- [ ] dependsOn arrays document logical dependencies
- [ ] blockedBy arrays only used when absolutely required
- [ ] All tasks use status: "pending"
- [ ] All timestamps in ISO 8601 format
- [ ] metadata.taskMasterVersion is "1.0"
- [ ] Saved to `.taskmaster/tasks/tasks.json`
