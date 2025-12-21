# Plan Schema

Reference for the plan.json file structure.

## Overview

A plan.json file contains:

- **meta**: Project metadata
- **summary**: Calculated progress statistics
- **phases**: Array of phases, each containing tasks
- **decisions**: Pending and resolved decisions (optional)
- **success_metrics**: Target metrics (optional)
- **blockers**: Active blockers (optional)

## Minimal Example

```json
{
  "meta": {
    "project": "My Project",
    "version": "1.0.0",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "business_plan_path": "docs/plan.md"
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
          "agent_type": null,
          "depends_on": [],
          "tracking": {}
        }
      ]
    }
  ]
}
```

## JSON Schema Reference

The canonical schema that `pv validate` uses:

```{literalinclude} ../../src/plan_view/plan.schema.json
:language: json
```

## Quick Reference

### Meta Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project` | string | Yes | Project name |
| `version` | string | Yes | Plan version (semver: `X.Y.Z`) |
| `schema_version` | string | No | Schema version for migrations |
| `created_at` | string | Yes | ISO 8601 creation timestamp |
| `updated_at` | string | Yes | ISO 8601 last update timestamp |
| `business_plan_path` | string | Yes | Path to business plan document |

### Summary Object

Automatically calculated by pv when saving:

| Field | Type | Description |
|-------|------|-------------|
| `total_phases` | integer | Number of phases |
| `total_tasks` | integer | Total tasks across all phases |
| `completed_tasks` | integer | Number of completed tasks |
| `in_progress_tasks` | integer | Currently active tasks |
| `blocked_tasks` | integer | Blocked tasks |
| `overall_progress` | number | Percentage complete (0-100) |

### Phase Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique phase identifier |
| `name` | string | Yes | Phase name |
| `description` | string | Yes | Phase description |
| `status` | string | Yes | pending, in_progress, completed, blocked, skipped |
| `progress` | object | Yes | `{completed, total, percentage}` |
| `tasks` | array | Yes | Array of task objects |

#### Special Phase IDs

- `deferred`: Tasks postponed for later consideration
- `99`: Bug tracking phase (convention)

### Task Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Task ID format: `phase.section.task` |
| `title` | string | Yes | Task title |
| `status` | string | Yes | pending, in_progress, completed, blocked, skipped |
| `agent_type` | string/null | Yes | Agent type or null |
| `depends_on` | array | Yes | Task IDs this depends on |
| `tracking` | object | Yes | Timestamps and metadata |
| `priority` | string/null | No | null, low, medium, high |
| `estimated_minutes` | integer/null | No | Estimated time |
| `subtasks` | array | No | Nested subtask objects |
| `business_plan_ref` | object/null | No | Reference to business plan section |

### Tracking Object

| Field | Type | Description |
|-------|------|-------------|
| `started_at` | string/null | ISO 8601 start timestamp |
| `completed_at` | string/null | ISO 8601 completion timestamp |
| `time_spent_minutes` | integer/null | Actual time spent |
| `notes` | string/null | Free-form notes |
| `attempts` | integer | Number of attempts (default: 0) |
| `last_error` | string/null | Last error message |
| `assigned_agent_id` | string/null | Agent instance ID |

### Valid Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not started |
| `in_progress` | Currently being worked on |
| `completed` | Finished successfully |
| `blocked` | Cannot proceed |
| `skipped` | Intentionally skipped |

### Priority Values

| Priority | Meaning |
|----------|---------|
| `null` | No priority set (default) |
| `low` | Low priority |
| `medium` | Medium priority |
| `high` | High priority |

## Task ID Format

Task IDs follow the pattern `phase.section.task`:

```
0.1.1  -> Phase 0, section 1, task 1
1.2.3  -> Phase 1, section 2, task 3
99.1.5 -> Bugs phase, section 1, task 5
```

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

Any non-empty string is valid, or `null` for unassigned.

## Example Files

The repository includes example plans:

- `examples/simple.json`: Basic project with 3 phases, 5 tasks
- `examples/complex.json`: Full-featured example with priorities, estimates, decisions

Explore them:

```bash
pv -f examples/simple.json
pv -f examples/complex.json summary
```
