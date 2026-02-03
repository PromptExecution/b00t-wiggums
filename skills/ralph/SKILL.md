---
name: ralph
description: "Convert PRDs to TaskMaster tasks.json format for the Ralph autonomous agent system. Use when you have an existing PRD and need to convert it to Ralph's TaskMaster format. Triggers on: convert this prd, turn this into ralph format, create tasks.json from this, ralph json, taskmaster format."
user-invocable: true
---

# Ralph TaskMaster Converter

Converts existing PRDs to the `.taskmaster/tasks/tasks.json` format that Ralph uses for autonomous execution with TaskMaster integration.

---

## The Job

Take a PRD (markdown file or text) and convert it to `tasks.json` in your `.taskmaster/tasks/` directory.

---

## Output Format

```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "[Story title]",
      "description": "As a [user], I want [feature] so that [benefit].\n\n[Additional context about implementation approach, patterns to follow, constraints]",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": [
        "Criterion 1",
        "Criterion 2",
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
    "description": "[Feature description from PRD title/intro]",
    "taskMasterVersion": "1.0"
  }
}
```

### Field Descriptions:

- **id**: Sequential task-001, task-002, etc.
- **title**: Short descriptive name (imperative form, e.g., "Add status field to database")
- **description**: Full user story with "As a [user], I want [feature] so that [benefit]" plus implementation details
- **status**: Always "pending" for new tasks
- **priority**: Numbered by dependency order (1 = must do first)
- **acceptanceCriteria**: Array of verifiable checkpoints
- **dependsOn**: Array of task IDs this task logically depends on (for documentation)
- **blockedBy**: Array of task IDs that must complete before this one can start (enforced by Ralph)
- **subtasks**: Empty array (reserved for future use)
- **notes**: Empty array (Ralph adds notes as it works)
- **createdAt/updatedAt**: ISO 8601 timestamps

---

## Story Size: The Number One Rule

**Each story must be completable in ONE Ralph iteration (one context window).**

Ralph spawns a fresh Amp instance per iteration with no memory of previous work. If a story is too big, the LLM runs out of context before finishing and produces broken code.

### Right-sized stories:
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

### Too big (split these):
- "Build the entire dashboard" - Split into: schema, queries, UI components, filters
- "Add authentication" - Split into: schema, middleware, login UI, session handling
- "Refactor the API" - Split into one story per endpoint or pattern

**Rule of thumb:** If you cannot describe the change in 2-3 sentences, it is too big.

---

## Story Ordering: Dependencies First

Tasks execute in priority order. Earlier tasks must not depend on later ones.

**Correct order:**
1. Schema/database changes (migrations)
2. Server actions / backend logic
3. UI components that use the backend
4. Dashboard/summary views that aggregate data

**Wrong order:**
1. UI component (depends on schema that does not exist yet)
2. Schema change

---

## Dependency Tracking: dependsOn vs blockedBy

TaskMaster supports two types of dependencies:

- **dependsOn**: Documentary field showing logical dependencies (for human understanding)
- **blockedBy**: Enforced by Ralph - task cannot start until blocking tasks are done

**Example:**
```json
{
  "id": "task-003",
  "title": "Add status toggle to UI",
  "dependsOn": ["task-001", "task-002"],  // Needs schema + badge component
  "blockedBy": []  // Can start once priority allows it
}
```

**When to use blockedBy:**
- Task B cannot compile/run without Task A completing first
- Task B would fail all tests without Task A's changes
- Task B modifies code that Task A creates

**When to use dependsOn only:**
- Task B logically builds on Task A but could theoretically be attempted
- Helps Ralph understand context but doesn't prevent execution
- Documents architectural relationships

---

## Acceptance Criteria: Must Be Verifiable

Each criterion must be something Ralph can CHECK, not something vague.

### Good criteria (verifiable):
- "Add `status` column to tasks table with default 'pending'"
- "Filter dropdown has options: All, Active, Completed"
- "Clicking delete shows confirmation dialog"
- "Typecheck passes"
- "Tests pass"

### Bad criteria (vague):
- "Works correctly"
- "User can do X easily"
- "Good UX"
- "Handles edge cases"

### Always include as final criterion:
```
"Typecheck passes"
```

For stories with testable logic, also include:
```
"Tests pass"
```

### For stories that change UI, also include:
```
"Verify in browser using dev-browser skill"
```

Frontend stories are NOT complete until visually verified. Ralph will use the dev-browser skill to navigate to the page, interact with the UI, and confirm changes work.

---

## Conversion Rules

1. **Each user story becomes one JSON entry**
2. **IDs**: Sequential (US-001, US-002, etc.)
3. **Priority**: Based on dependency order, then document order
4. **All stories**: `passes: false` and empty `notes`
5. **branchName**: Derive from feature name, kebab-case, prefixed with `ralph/`
6. **Always add**: "Typecheck passes" to every story's acceptance criteria

---

## Splitting Large PRDs

If a PRD has big features, split them:

**Original:**
> "Add user notification system"

**Split into:**
1. US-001: Add notifications table to database
2. US-002: Create notification service for sending notifications
3. US-003: Add notification bell icon to header
4. US-004: Create notification dropdown panel
5. US-005: Add mark-as-read functionality
6. US-006: Add notification preferences page

Each is one focused change that can be completed and verified independently.

---

## Example

**Input PRD:**
```markdown
# Task Status Feature

Add ability to mark tasks with different statuses.

## Requirements
- Toggle between pending/in-progress/done on task list
- Filter list by status
- Show status badge on each task
- Persist status in database
```

**Output tasks.json:**
```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Add status field to tasks table",
      "description": "As a developer, I need to store task status in the database so that users can track progress on their tasks.\n\nImplementation: Add a status enum column to the tasks table with values: 'pending', 'in_progress', 'done'. Default to 'pending' for new tasks.",
      "status": "pending",
      "priority": 1,
      "acceptanceCriteria": [
        "Add status column: 'pending' | 'in_progress' | 'done' (default 'pending')",
        "Generate and run migration successfully",
        "Typecheck passes"
      ],
      "dependsOn": [],
      "blockedBy": [],
      "subtasks": [],
      "notes": [],
      "createdAt": "2026-02-03T00:00:00Z",
      "updatedAt": "2026-02-03T00:00:00Z"
    },
    {
      "id": "task-002",
      "title": "Display status badge on task cards",
      "description": "As a user, I want to see task status at a glance so I know which tasks are in progress.\n\nImplementation: Add colored badge component to task card. Use existing badge component with color variants: gray=pending, blue=in_progress, green=done.",
      "status": "pending",
      "priority": 2,
      "acceptanceCriteria": [
        "Each task card shows colored status badge",
        "Badge colors: gray=pending, blue=in_progress, green=done",
        "Typecheck passes",
        "Verify in browser using dev-browser skill"
      ],
      "dependsOn": ["task-001"],
      "blockedBy": [],
      "subtasks": [],
      "notes": [],
      "createdAt": "2026-02-03T00:00:00Z",
      "updatedAt": "2026-02-03T00:00:00Z"
    },
    {
      "id": "task-003",
      "title": "Add status toggle to task list rows",
      "description": "As a user, I want to change task status directly from the list so I can quickly update progress without opening the full task.\n\nImplementation: Add dropdown or toggle to each task row. Use optimistic updates for immediate UI feedback. Save via server action.",
      "status": "pending",
      "priority": 3,
      "acceptanceCriteria": [
        "Each row has status dropdown or toggle",
        "Changing status saves immediately",
        "UI updates without page refresh",
        "Typecheck passes",
        "Verify in browser using dev-browser skill"
      ],
      "dependsOn": ["task-001", "task-002"],
      "blockedBy": [],
      "subtasks": [],
      "notes": [],
      "createdAt": "2026-02-03T00:00:00Z",
      "updatedAt": "2026-02-03T00:00:00Z"
    },
    {
      "id": "task-004",
      "title": "Filter tasks by status",
      "description": "As a user, I want to filter the list to see only certain statuses so I can focus on specific types of work.\n\nImplementation: Add filter dropdown to list header. Persist filter state in URL params. Show empty state when no tasks match filter.",
      "status": "pending",
      "priority": 4,
      "acceptanceCriteria": [
        "Filter dropdown: All | Pending | In Progress | Done",
        "Filter persists in URL params",
        "Empty state message when no tasks match",
        "Typecheck passes",
        "Verify in browser using dev-browser skill"
      ],
      "dependsOn": ["task-002"],
      "blockedBy": [],
      "subtasks": [],
      "notes": [],
      "createdAt": "2026-02-03T00:00:00Z",
      "updatedAt": "2026-02-03T00:00:00Z"
    }
  ],
  "metadata": {
    "project": "TaskApp",
    "branchName": "ralph/task-status",
    "description": "Task Status Feature - Track task progress with status indicators",
    "taskMasterVersion": "1.0"
  }
}
```

---

## Archiving Previous Runs

**Before writing a new tasks.json, check if there is an existing one from a different feature:**

1. Read the current `tasks.json` if it exists
2. Check if `branchName` differs from the new feature's branch name
3. If different AND `progress.txt` has content beyond the header:
   - Create archive folder: `archive/YYYY-MM-DD-feature-name/`
   - Copy current `tasks.json` and `progress.txt` to archive
   - Reset `progress.txt` with fresh header

**The ralph.sh script handles this automatically** when you run it, but if you are manually updating tasks.json between runs, archive first.

---

## Checklist Before Saving

Before writing tasks.json to `.taskmaster/tasks/tasks.json`, verify:

- [ ] **Previous run archived** (if tasks.json exists with different branchName, archive it first)
- [ ] Each task is completable in one iteration (small enough)
- [ ] Tasks are ordered by dependency (schema to backend to UI)
- [ ] Priority numbers reflect dependency order (1 = first, 2 = second, etc.)
- [ ] Every task has "Typecheck passes" as criterion
- [ ] UI tasks have "Verify in browser using dev-browser skill" as criterion
- [ ] Acceptance criteria are verifiable (not vague)
- [ ] No task depends on a later task (check priority order)
- [ ] **dependsOn** arrays list logical dependencies for each task
- [ ] **blockedBy** arrays only used when task cannot execute without blocker
- [ ] All task IDs use format: task-001, task-002, etc.
- [ ] metadata.taskMasterVersion is "1.0"
- [ ] All status fields are "pending"
- [ ] timestamps use ISO 8601 format
