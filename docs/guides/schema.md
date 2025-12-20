# Plan Schema

Understanding the structure of plan.json files.

## Overview

A plan.json file contains:

- **meta**: Project metadata
- **summary**: Calculated progress statistics
- **phases**: Array of phases, each containing tasks

## Full Schema

```json
{
  "meta": {
    "project": "Project Name",
    "version": "1.0.0",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "business_plan_path": ".claude/BUSINESS_PLAN.md"
  },
  "summary": {
    "total_phases": 3,
    "total_tasks": 10,
    "completed_tasks": 5,
    "overall_progress": 50.0
  },
  "phases": [
    {
      "id": "0",
      "name": "Phase Name",
      "description": "Phase description",
      "status": "in_progress",
      "progress": {
        "completed": 2,
        "total": 4,
        "percentage": 50.0
      },
      "tasks": [
        {
          "id": "0.1.1",
          "title": "Task title",
          "status": "completed",
          "agent_type": "python-backend-engineer",
          "depends_on": [],
          "tracking": {
            "started_at": "2024-01-01T10:00:00Z",
            "completed_at": "2024-01-01T11:00:00Z"
          }
        }
      ]
    }
  ]
}
```

## Meta Object

| Field | Type | Description |
|-------|------|-------------|
| `project` | string | Project name |
| `version` | string | Plan version (semver) |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |
| `business_plan_path` | string | Optional path to business plan doc |

## Summary Object

Automatically calculated by pv when saving:

| Field | Type | Description |
|-------|------|-------------|
| `total_phases` | integer | Number of phases |
| `total_tasks` | integer | Total tasks across all phases |
| `completed_tasks` | integer | Number of completed tasks |
| `overall_progress` | number | Percentage complete (0-100) |

## Phase Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique phase identifier (typically "0", "1", etc.) |
| `name` | string | Phase name |
| `description` | string | Phase description |
| `status` | string | pending, in_progress, completed, blocked, skipped |
| `progress` | object | Calculated progress for this phase |
| `tasks` | array | Array of task objects |

## Task Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique task ID (format: `phase.section.task`) |
| `title` | string | Task title/description |
| `status` | string | pending, in_progress, completed, blocked, skipped |
| `agent_type` | string | Optional agent type for the task |
| `depends_on` | array | Array of task IDs this task depends on |
| `tracking` | object | Timestamps for started_at and completed_at |

## Task ID Format

Task IDs follow the pattern `phase.section.task`:

- `0.1.1` - Phase 0, section 1, task 1
- `1.2.3` - Phase 1, section 2, task 3

This hierarchical format allows logical grouping within phases.

## Valid Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Not started, waiting |
| `in_progress` | Currently being worked on |
| `completed` | Finished successfully |
| `blocked` | Cannot proceed (dependency/issue) |
| `skipped` | Intentionally skipped |

## Auto-Calculated Fields

When you save a plan (via any edit command), pv automatically:

1. Updates `meta.updated_at` to current timestamp
2. Recalculates `progress` for each phase
3. Recalculates the `summary` totals
4. Updates phase `status` based on task completion

## Validation

Use `pv validate` to check your plan.json against the schema:

```bash
pv validate
# ✅ plan.json is valid

pv validate --json
# {"valid": true, "path": "plan.json"}
```

Invalid plans show the specific error:

```bash
pv validate
# ❌ Validation failed for plan.json:
#    'status' is a required property
#    Path: phases.0.tasks.0
```

## Agent Types

Common agent types for AI workflows:

- `general-purpose` - Default, general tasks
- `python-backend-engineer` - Python backend development
- `ui-engineer` - Frontend/UI development
- `github-git-expert` - Git operations, PR management
- `documentation-expert` - Documentation tasks
- `software-architect` - Architecture decisions
- `python-tester` - Testing tasks

These are suggestions; you can use any string value.
