# Plan Schema

Reference for the plan.json file structure.

## Overview

A plan.json file contains:

- **meta**: Project metadata
- **summary**: Calculated progress statistics
- **phases**: Array of phases, each containing tasks

## Minimal Example

```json
{
  "meta": {
    "project": "My Project",
    "version": "1.0.0",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "summary": {
    "total_phases": 1,
    "total_tasks": 1,
    "completed_tasks": 0,
    "overall_progress": 0
  },
  "phases": [
    {
      "id": "0",
      "name": "Setup",
      "description": "Initial setup",
      "status": "pending",
      "progress": { "completed": 0, "total": 1, "percentage": 0 },
      "tasks": [
        {
          "id": "0.1.1",
          "title": "Initialize project",
          "status": "pending",
          "depends_on": [],
          "tracking": {}
        }
      ]
    }
  ]
}
```

## Full Schema

See `examples/complex.json` for a complete example with all optional fields.

## Meta Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | Yes | Project name |
| `version` | string | Yes | Plan version (semver) |
| `created_at` | string | Yes | ISO 8601 creation timestamp |
| `updated_at` | string | Yes | ISO 8601 last update timestamp |
| `business_plan_path` | string | No | Path to business plan document |

## Summary Object

Automatically calculated by pv when saving:

| Field | Type | Description |
|-------|------|-------------|
| `total_phases` | integer | Number of phases |
| `total_tasks` | integer | Total tasks across all phases |
| `completed_tasks` | integer | Number of completed tasks |
| `overall_progress` | number | Percentage complete (0-100) |

## Phase Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique phase identifier |
| `name` | string | Yes | Phase name |
| `description` | string | Yes | Phase description |
| `status` | string | Yes | pending, in_progress, completed, blocked, skipped |
| `progress` | object | Yes | Calculated progress for this phase |
| `tasks` | array | Yes | Array of task objects |

### Special Phase IDs

- `deferred`: Tasks postponed for later consideration
- `99`: Bug tracking phase (convention)

## Task Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique task ID (format: `phase.section.task`) |
| `title` | string | Yes | Task title |
| `status` | string | Yes | pending, in_progress, completed, blocked, skipped |
| `agent_type` | string | No | Agent type for the task |
| `depends_on` | array | Yes | Array of task IDs this task depends on |
| `tracking` | object | Yes | Timestamps for started_at and completed_at |
| `priority` | string | No | critical, high, medium, low |
| `estimated_minutes` | integer | No | Estimated time to complete |
| `subtasks` | array | No | Nested subtask objects |

## Task ID Format

Task IDs follow the pattern `phase.section.task`:

```
0.1.1  -> Phase 0, section 1, task 1
1.2.3  -> Phase 1, section 2, task 3
99.1.5 -> Bugs phase, section 1, task 5
```

## Valid Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Finished successfully |
| `blocked` | Cannot proceed |
| `skipped` | Intentionally skipped |

## Auto-Calculated Fields

When saving a plan (via any edit command), pv automatically:

1. Updates `meta.updated_at` to current timestamp
2. Recalculates `progress` for each phase
3. Recalculates the `summary` totals
4. Updates phase `status` based on task completion

## Validation

Use `pv validate` to check your plan.json against the schema:

```bash
$ pv validate
plan.json is valid

$ pv validate --json
{"valid": true, "path": "plan.json"}
```

Invalid plans show the specific error:

```bash
$ pv validate
Validation failed for plan.json:
   'status' is a required property
   Path: phases.0.tasks.0
```

## Agent Types

Agent types are flexible strings. Common conventions:

| Type | Use Case |
|------|----------|
| `general-purpose` | Default, general tasks |
| `python-backend-engineer` | Python backend development |
| `ui-engineer` | Frontend/UI development |
| `github-git-expert` | Git operations, PR management |
| `documentation-expert` | Documentation tasks |
| `software-architect` | Architecture decisions |
| `python-tester` | Testing tasks |

Any kebab-case string is valid: `^[a-z][a-z0-9-]*$`

## Example Files

The repository includes example plans:

- `examples/simple.json`: Basic project with 3 phases, 5 tasks
- `examples/complex.json`: Full-featured example with priorities, estimates, decisions

Explore them:

```bash
pv -f examples/simple.json
pv -f examples/complex.json summary
```
