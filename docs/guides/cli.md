# CLI Reference

Complete reference for all pv commands.

## Global Options

| Option | Description |
|--------|-------------|
| `-f, --file FILE` | Path to plan.json (default: `./plan.json`) |
| `--json` | Output as JSON (view commands only) |
| `-q, --quiet` | Suppress output (edit commands only) |
| `-d, --dry-run` | Preview changes without saving |
| `-h, --help` | Show help message |

## View Commands

### Overview (default)

Show full plan with all phases and tasks:

```bash
pv
pv -f examples/simple.json
```

Output:

```
API Backend v1.0.0
Progress: 40% (2/5 tasks)

Phase 0: Setup (100%)
   Project initialization and configuration

   [0.1.1] Initialize repository (github-git-expert)
   [0.1.2] Configure CI/CD pipeline (github-git-expert)

Phase 1: Core Features (0%)
   Implement primary application features

   [1.1.1] Create user authentication (python-backend-engineer)
   [1.1.2] Build REST API endpoints (python-backend-engineer)

Phase 2: Testing (0%)
   Test coverage and validation

   [2.1.1] Write unit tests (python-tester)
```

### Current (`c`, `current`)

Show completed phases summary, current phase, and next task:

```bash
pv current
pv c --json
```

### Next (`n`, `next`)

Show the next task to work on (respects dependencies):

```bash
pv next
pv n -f examples/simple.json
```

Output:

```
Next Task:
  [1.1.1] Create user authentication
  Phase: Core Features
  Agent: python-backend-engineer
  Depends on: 0.1.2
```

### Phase (`p`, `phase`)

Show current phase details with all tasks and dependencies:

```bash
pv phase
pv p --json
```

### Get (`g`, `get`)

Show a specific task or phase by ID:

```bash
pv get 0.1.1
pv g 1          # Show phase 1
pv get 1.1 --json
```

Partial ID matching is supported. If `1.1.1` is the only task starting with `1`, then `pv get 1` will find it.

### Last (`l`, `last`)

Show recently completed tasks:

```bash
pv last           # Last 5 completed
pv last -n 10     # Last 10 completed
pv last -a        # All completed
pv l --json
```

### Future (`f`, `future`)

Show upcoming tasks (pending/in_progress/blocked), with actionable tasks first:

```bash
pv future         # Next 5 upcoming tasks
pv future -n 10   # Next 10 upcoming tasks
pv future -a      # All upcoming tasks
pv f --json
```

Output shows tasks prioritized by:
1. In-progress tasks (🔄)
2. Actionable pending tasks - dependencies met (👉)
3. Waiting pending tasks - dependencies not met (⏳)
4. Blocked tasks (🚫)

### Summary (`s`, `summary`)

Show plan progress summary:

```bash
pv summary
pv s --json
```

Output:

```
API Backend v1.0.0
Overall Progress: 40.0% (2/5 tasks)

Phase Breakdown:
  Phase 0: Setup
     100.0% (2/2 tasks)
  Phase 1: Core Features
     0.0% (0/2 tasks)
  Phase 2: Testing
     0.0% (0/1 tasks)
```

### Bugs (`b`, `bugs`)

Show the bugs phase:

```bash
pv bugs
pv b -f examples/complex.json
```

### Deferred (`d`, `deferred`)

Show the deferred phase:

```bash
pv deferred
pv d --json
```

### Ideas (`i`, `ideas`)

Show the ideas phase:

```bash
pv ideas
pv i --json
```

### Validate (`v`, `validate`)

Validate plan.json against the schema:

```bash
pv validate
pv v -f examples/complex.json --json
```

Output:

```
plan.json is valid
```

## Edit Commands

### Init

Create a new plan.json:

```bash
pv init "Project Name"
pv init "My App" --force  # Overwrite existing
pv init "Test" --dry-run  # Preview only
```

### Add Phase

Add a new phase:

```bash
pv add-phase "Phase Name"
pv add-phase "Setup" --desc "Project setup tasks"
pv add-phase "Auth" -q      # Quiet mode
```

### Add Task

Add a task to a phase:

```bash
pv add-task 0 "Task title"
pv add-task 0 "Create model" --agent python-backend-engineer
pv add-task 1 "Write tests" --deps 1.1.1,1.1.2
```

Options:

| Option | Description |
|--------|-------------|
| `--agent TYPE` | Agent type for the task |
| `--deps ID,ID,...` | Comma-separated dependency task IDs |

### Set

Set a task field:

```bash
pv set 0.1.1 status blocked
pv set 0.1.1 agent python-backend-engineer
pv set 0.1.1 title "Updated title"
```

Fields:

| Field | Valid Values |
|-------|--------------|
| `status` | pending, in_progress, completed, blocked, skipped |
| `agent` | Any string, or "none" to clear |
| `title` | Any string |

### Done

Mark a task as completed:

```bash
pv done 0.1.1
pv done 1 -q    # Quiet mode, partial ID match
```

### Start

Mark a task as in_progress:

```bash
pv start 0.1.1
```

### Block

Mark a task as blocked:

```bash
pv block 0.1.1
```

### Skip

Mark a task as skipped:

```bash
pv skip 0.1.1
```

### Defer

Move a task to the deferred phase, or create a new deferred task:

```bash
pv defer 0.1.1                              # Move existing task
pv defer "Research caching"                 # Create new deferred task
pv defer 0.1.1 -r "Waiting for API docs"    # With reason
pv defer 0.1.1 --reason "Low priority"      # Long form
```

The reason is displayed in `pv deferred` and `pv get` output.

### Bug

Move a task to the bugs phase, or create a new bug:

```bash
pv bug 0.1.1                    # Move existing task
pv bug "Login fails on Safari"  # Create new bug
```

### Idea

Move a task to the ideas phase, or create a new idea:

```bash
pv idea 0.1.1                   # Move existing task
pv idea "Add dark mode toggle"  # Create new idea
```

### Compact

Archive completed tasks to a backup file and shrink the plan:

```bash
pv compact                  # Create backup, remove completed tasks
pv compact -n 10            # Keep max 10 backups
pv compact --dry-run        # Preview what would be archived
```

### Remove (`rm`)

Remove a phase or task:

```bash
pv rm task 0.1.1
pv rm phase 2
pv rm task 1 --dry-run  # Preview only
```

## Status Icons

| Status | Icon |
|--------|------|
| completed | Done |
| in_progress | In progress |
| pending | Waiting |
| blocked | Blocked |
| skipped | Skipped |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NO_COLOR` | Disable colored output (any value) |
| `FORCE_COLOR` | Force colored output even in pipes |

## Examples

### Typical Workflow

```bash
# Initialize
pv init "API Backend"

# Add phases
pv add-phase "Models" --desc "Database models"
pv add-phase "Endpoints" --desc "REST API endpoints"
pv add-phase "Tests" --desc "Test coverage"

# Add tasks with dependencies
pv add-task 0 "User model" --agent python-backend-engineer
pv add-task 0 "Session model" --agent python-backend-engineer
pv add-task 1 "Auth endpoints" --deps 0.1.1
pv add-task 2 "Unit tests" --deps 1.1.1

# Work through tasks
pv start 0.1.1
pv done 0.1.1
pv next   # Shows 0.1.2 or 1.1.1 based on dependencies
```

### JSON Output for Scripts

```bash
# Get next task as JSON
NEXT=$(pv next --json)
TASK_ID=$(echo "$NEXT" | jq -r '.id')
AGENT=$(echo "$NEXT" | jq -r '.agent_type')

# Process and mark complete
pv done "$TASK_ID" -q
```

### Working with Example Files

```bash
# Explore the simple example
pv -f examples/simple.json
pv -f examples/simple.json current
pv -f examples/simple.json next --json

# Explore the complex example
pv -f examples/complex.json summary
pv -f examples/complex.json bugs
pv -f examples/complex.json deferred
```

### Using Dry-Run Mode

Preview changes before applying them:

```bash
pv init "Test Project" --dry-run
# Would: Created plan.json for 'Test Project'

pv done 0.1.1 --dry-run
# Would: [0.1.1] status -> completed
```
