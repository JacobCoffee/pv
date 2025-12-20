# CLI Reference

Complete reference for all pv commands.

## Global Options

These options work with all commands:

| Option | Description |
|--------|-------------|
| `-f, --file FILE` | Path to plan.json (default: `./plan.json`) |
| `--json` | Output as JSON (view commands only) |
| `-h, --help` | Show help message |

## View Commands

### Overview (default)

Show full plan with all phases and tasks:

```bash
pv
pv --json  # JSON output
```

### Current (`c`, `current`)

Show completed phases summary, current phase, and next task:

```bash
pv c
pv current --json
```

### Next (`n`, `next`)

Show the next task to work on (respects dependencies):

```bash
pv n
pv next --json
```

### Phase (`p`, `phase`)

Show current phase details with all tasks and dependencies:

```bash
pv p
pv phase --json
```

### Get (`g`, `get`)

Show a specific task by ID:

```bash
pv g 0.1.1
pv get 1.2.3 --json
```

### Last (`l`, `last`)

Show recently completed tasks:

```bash
pv l           # Last 5 completed
pv last -n 10  # Last 10 completed
pv last --json
```

### Validate (`v`, `validate`)

Validate plan.json against the schema:

```bash
pv v
pv validate --json
```

## Edit Commands

### Init

Create a new plan.json:

```bash
pv init "Project Name"
pv init "My App" --force  # Overwrite existing
```

### Add Phase

Add a new phase:

```bash
pv add-phase "Phase Name"
pv add-phase "Setup" --desc "Project setup tasks"
```

### Add Task

Add a task to a phase:

```bash
pv add-task PHASE_ID "Task title"
pv add-task 0 "Create model" --agent python-backend-engineer
pv add-task 1 "Write tests" --deps 1.1.1,1.1.2
```

Options:
- `--agent AGENT_TYPE`: Specify the agent type for the task
- `--deps ID,ID,...`: Comma-separated task IDs this task depends on

### Set

Set a task field:

```bash
pv set TASK_ID FIELD VALUE
```

Fields:
- `status`: pending, in_progress, completed, blocked, skipped
- `agent`: Agent type (or "none" to clear)
- `title`: Task title

Examples:

```bash
pv set 0.1.1 status blocked
pv set 0.1.1 agent python-backend-engineer
pv set 0.1.1 title "Updated title"
```

### Done

Mark a task as completed (shortcut for `set ID status completed`):

```bash
pv done 0.1.1
```

### Start

Mark a task as in_progress (shortcut for `set ID status in_progress`):

```bash
pv start 0.1.1
```

### Remove (`rm`)

Remove a phase or task:

```bash
pv rm task 0.1.1   # Remove a task
pv rm phase 2      # Remove a phase (and all its tasks)
```

## Status Icons

| Status | Icon |
|--------|------|
| completed | ✅ |
| in_progress | 🔄 |
| pending | ⏳ |
| blocked | 🛑 |
| skipped | ⏭️ |

## Examples

### Typical Workflow

```bash
# Initialize project
pv init "API Backend"

# Add phases
pv add-phase "Models" --desc "Database models"
pv add-phase "Endpoints" --desc "REST API endpoints"
pv add-phase "Tests" --desc "Test coverage"

# Add tasks
pv add-task 0 "User model" --agent python-backend-engineer
pv add-task 0 "Session model" --agent python-backend-engineer
pv add-task 1 "Auth endpoints" --agent python-backend-engineer --deps 0.1.1
pv add-task 2 "Unit tests" --agent python-tester --deps 1.1.1

# Work through tasks
pv start 0.1.1
# ... do work ...
pv done 0.1.1

# Check status
pv c  # Current progress
pv n  # Next task
```

### JSON Output for Scripts

```bash
# Get next task as JSON
NEXT=$(pv next --json)
TASK_ID=$(echo "$NEXT" | jq -r '.id')
AGENT=$(echo "$NEXT" | jq -r '.agent_type')

# Mark complete
pv done "$TASK_ID"
```

### Using a Different File

```bash
pv -f project.plan.json
pv -f ~/plans/backend.json c
```
